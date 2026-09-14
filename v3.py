import deezer

client = deezer.Client(headers={"Accept-Language": "pt-br"})


editorials = client.list_editorials()
print(editorials)
