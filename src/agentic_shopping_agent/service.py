from __future__ import annotations

from typing import Callable, Optional

from browser_use_sdk.v3 import AsyncBrowserUse

from agentic_shopping_agent.config import Settings, load_settings
from agentic_shopping_agent.models import (
    ProductVerification,
    PurchaseDecision,
    RankedOption,
    ShoppingRequest,
    ShoppingResearch,
    VerificationReport,
)
from agentic_shopping_agent.prompting import (
    build_shopping_task,
    build_verification_task,
    ensure_effective_criteria,
)
from agentic_shopping_agent.ranking import build_purchase_decision, rank_options


DEFAULT_SAFE_DOMAINS = (
    "amazon.com",
    "bestbuy.com",
    "walmart.com",
    "target.com",
    "costco.com",
    "newegg.com",
    "bhphotovideo.com",
    "apple.com",
    "samsung.com",
    "rei.com",
    "homedepot.com",
    "lowes.com",
    "wirecutter.com",
    "rtings.com",
    "pcmag.com",
    "cnet.com",
    "tomsguide.com",
)

TOP_CANDIDATES_TO_VERIFY = 3


class ShoppingAgentService:
    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or load_settings()
        self.client = AsyncBrowserUse(api_key=self.settings.browser_use_api_key)

    async def research_and_recommend(
        self,
        request: ShoppingRequest,
        show_live_url: bool = False,
        keep_session: bool = False,
        status_callback: Optional[Callable[[str], None]] = None,
    ) -> PurchaseDecision:
        self._emit_status(status_callback, "Preparing shopping brief")
        effective_domains = self._effective_allowed_domains(request)
        if effective_domains and not request.allowed_domains and not request.allow_open_web:
            self._emit_status(status_callback, "Browsing restricted to trusted shopping domains")
        elif request.allow_open_web:
            self._emit_status(status_callback, "Open web browsing explicitly enabled")

        criteria = ensure_effective_criteria(request.criteria)
        effective_request = request.model_copy(
            update={"allowed_domains": effective_domains, "criteria": criteria}
        )
        task = build_shopping_task(effective_request, criteria)

        session = None
        live_url = None
        run_kwargs = {
            "output_schema": ShoppingResearch,
            "proxy_country_code": request.proxy_country_code,
        }

        if effective_domains:
            run_kwargs["allowed_domains"] = effective_domains

        if show_live_url or keep_session:
            self._emit_status(status_callback, "Starting browser session")
            session = await self.client.sessions.create(
                proxy_country_code=request.proxy_country_code,
                keep_alive=keep_session,
            )
            live_url = getattr(session, "live_url", None)
            run_kwargs["session_id"] = session.id
            run_kwargs.pop("proxy_country_code", None)
            if live_url:
                self._emit_status(status_callback, f"Browser live view ready: {live_url}")

        try:
            self._emit_status(status_callback, "Researching products on the web")
            result = await self.client.run(task, **run_kwargs)
            if getattr(result, "output", None) is None:
                raise RuntimeError("Browser Use did not return structured shopping research.")
            research = (
                result.output
                if isinstance(result.output, ShoppingResearch)
                else ShoppingResearch.model_validate(result.output)
            )
            self._emit_status(status_callback, "Ranking options")
            initial_ranked_options = rank_options(effective_request, criteria, research)

            verification_report = None
            verification_lookup: dict[str, ProductVerification] = {}
            missing_information = list(research.missing_information)

            try:
                verification_candidates = initial_ranked_options[:TOP_CANDIDATES_TO_VERIFY]
                if verification_candidates:
                    self._emit_status(status_callback, "Verifying top candidates")
                    verification_report = await self._verify_top_candidates(
                        request=effective_request,
                        ranked_options=verification_candidates,
                        session_id=session.id if session is not None else None,
                    )
                    verification_lookup = self._verification_lookup(verification_report)
                    missing_information.extend(verification_report.missing_information)
            except Exception as exc:
                missing_information.append(
                    f"Verification pass failed before the final recommendation: {exc}"
                )
                self._emit_status(status_callback, "Verification pass failed, continuing with initial ranking")

            self._emit_status(status_callback, "Finalizing recommendation")
            ranked_options = rank_options(
                effective_request,
                criteria,
                research,
                verifications=verification_lookup,
            )
            return build_purchase_decision(
                request=effective_request,
                research=research,
                ranked_options=ranked_options,
                verification_report=verification_report,
                missing_information=missing_information,
                live_url=live_url,
            )
        finally:
            if session is not None and not keep_session:
                try:
                    await self.client.sessions.stop(session.id)
                except Exception:
                    pass

    @staticmethod
    def _emit_status(
        status_callback: Optional[Callable[[str], None]],
        message: str,
    ) -> None:
        if status_callback is not None:
            status_callback(message)

    @staticmethod
    def _effective_allowed_domains(request: ShoppingRequest) -> list[str]:
        if request.allowed_domains:
            return request.allowed_domains
        if request.allow_open_web:
            return []
        return list(DEFAULT_SAFE_DOMAINS)

    async def _verify_top_candidates(
        self,
        request: ShoppingRequest,
        ranked_options: list[RankedOption],
        session_id: Optional[str] = None,
    ) -> VerificationReport:
        task = build_verification_task(request, ranked_options)
        run_kwargs = {
            "output_schema": VerificationReport,
            "proxy_country_code": request.proxy_country_code,
        }

        if request.allowed_domains:
            run_kwargs["allowed_domains"] = request.allowed_domains

        if session_id is not None:
            run_kwargs["session_id"] = session_id
            run_kwargs.pop("proxy_country_code", None)

        result = await self.client.run(task, **run_kwargs)
        if getattr(result, "output", None) is None:
            raise RuntimeError("Browser Use did not return verification results.")

        if isinstance(result.output, VerificationReport):
            return result.output

        return VerificationReport.model_validate(result.output)

    @staticmethod
    def _verification_lookup(
        verification_report: VerificationReport,
    ) -> dict[str, ProductVerification]:
        lookup: dict[str, ProductVerification] = {}

        for check in verification_report.checks:
            lookup[check.product_url.strip().casefold()] = check
            lookup.setdefault(check.product_name.strip().casefold(), check)

        return lookup
