
from locust import HttpUser, task, between
from locust.exception import StopUser


class RAGUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # Use the email registered in your RAG application
        response = self.client.post(
            "/token",
            data={
                "username": "user@example.com",
                "password": "stringst"
            },
            name="/token"
        )

        if response.status_code != 200:
            print("LOGIN FAILED:", response.status_code, response.text)
            raise StopUser()

        token = response.json().get("access_token")

        if not token:
            print("TOKEN MISSING:", response.text)
            raise StopUser()

        self.client.headers.update({
            "Authorization": f"Bearer {token}"
        })

    @task
    def ask_question(self):
        payload = {
            "document_id": "9539a437-c9aa-4900-858e-bddc479429c2",
            "question": "Summarize the document's main subject and key points."
        }

        with self.client.post(
            "/ask_query",
            json=payload,
            catch_response=True,
            name="/ask_query"
        ) as response:

            if response.status_code == 200:
                response.success()
            else:
                response.failure(
                    f"HTTP {response.status_code}: {response.text}"
                )
