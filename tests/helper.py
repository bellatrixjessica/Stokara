PASSWORD = "rahasia123"


def login(client, username, password=PASSWORD):
    return client.post("/api/login", json={"username": username, "password": password})
