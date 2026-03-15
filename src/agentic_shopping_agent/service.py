from __future__ import annotations

from typing import Callable, Optional

from browser_use_sdk.v3 import AsyncBrowserUse

from agentic_shopping_agent.config import Settings, load_settings
from agentic_shopping_agent.models import PurchaseDecision, ShoppingRequest, ShoppingResearch
from agentic_shopping_agent.prompting import build_shopping_task, ensure_effective_criteria
from agentic_shopping_agent.ranking import build_purchase_decision, rank_options


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
        criteria = ensure_effective_criteria(request.criteria)
        task = build_shopping_task(request, criteria)

        session = None
        live_url = None
        run_kwargs = {"output_schema": ShoppingResearch}

        if request.allowed_domains:
            run_kwargs["allowed_domains"] = request.allowed_domains

        if show_live_url or keep_session or request.proxy_country_code:
            self._emit_status(status_callback, "Starting browser session")
            session = await self.client.sessions.create(
                proxy_country_code=request.proxy_country_code,
                keep_alive=keep_session,
            )
            live_url = getattr(session, "live_url", None)
            run_kwargs["session_id"] = session.id
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
            ranked_options = rank_options(request, criteria, research)
            return build_purchase_decision(
                request=request,
                research=research,
                ranked_options=ranked_options,
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
