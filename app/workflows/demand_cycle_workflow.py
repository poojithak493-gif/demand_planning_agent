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
    async def run(self, distributor_id: str, distributor_email: str):
        context = await workflow.execute_activity(
            fetch_distributor_context_activity,
            distributor_id,
            start_to_close_timeout=timedelta(minutes=2),
        )

        recommendations = await workflow.execute_activity(
            graph_recommendation_activity,
            distributor_id,
            start_to_close_timeout=timedelta(minutes=2),
        )

        email_payload = await workflow.execute_activity(
            build_email_activity,
            args=[context, recommendations],
            start_to_close_timeout=timedelta(minutes=2),
        )

        send_result = await workflow.execute_activity(
            send_email_activity,
            args=[distributor_email, email_payload],
            start_to_close_timeout=timedelta(minutes=2),
        )

        return {
            "distributor_id": distributor_id,
            "email_sent": True,
            "send_result": send_result,
            "recommendations_count": len(recommendations["recommendations"]),
        }