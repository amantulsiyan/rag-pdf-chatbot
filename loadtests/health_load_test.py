
from locust import HttpUser, task, constant


class HealthUser(HttpUser):

    # No artificial waiting between requests
    wait_time = constant(0)

    @task
    def health_check(self):

        with self.client.get(
            "/health",
            name="GET /health",
            catch_response=True
        ) as response:

            if response.status_code != 200:
                response.failure(
                    f"Unexpected status: {response.status_code}"
                )
            else:
                response.success()
