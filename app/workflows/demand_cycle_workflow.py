from datetime import timedelta
from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from app.workflows.activities import (
        fetch_distributor_context_activity,
        graph_recommendation_activity,
        build_email_activity,
        send_email_activity,
    )


@workflow.defn
class DemandCycleWorkflow:
    @workflow.run
    async def run(self, distributor_code: str):
        context = await workflow.execute_activity(
            fetch_distributor_context_activity,
            distributor_code,
            start_to_close_timeout=timedelta(minutes=2),
        )

        recommendations = await workflow.execute_activity(
            graph_recommendation_activity,
            distributor_code,
            start_to_close_timeout=timedelta(minutes=2),
        )

        email_payload = await workflow.execute_activity(
            build_email_activity,
            distributor_code,
            start_to_close_timeout=timedelta(minutes=2),
        )

        send_result = await workflow.execute_activity(
            send_email_activity,
            distributor_code,
            start_to_close_timeout=timedelta(minutes=2),
        )

        return {
            "distributor_code": distributor_code,
            "distributor_email": context["email"],
            "email_sent": True,
            "send_result": send_result,
            "recommendations_count": len(recommendations["recommended_skus"]),
            "email_payload": email_payload,
        }
