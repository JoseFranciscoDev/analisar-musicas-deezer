import requests
import csv
import time

PAISES = ["Colombia", "Uruguay", "Argentina", "Peru"]
BASE_URL = "https://api.deezer.com"


def buscar_playlist(pais):
    """Busca playlists com o termo 'Top <País>' e retorna as opções encontradas."""
    resp = requests.get(f"{BASE_URL}/search/playlist", params={"q": f"Top {pais}"})
    resp.raise_for_status()
    data = resp.json().get("data", [])
    return data


def escolher_playlist_oficial(resultados, pais):
    """
    Tenta identificar automaticamente a playlist oficial do Deezer
    (geralmente criada pelo usuário 'Deezer' e com nome parecido com 'Top Colombia').
    Se não achar com confiança, mostra as opções para você escolher manualmente.
    """
    candidatas = []
    for p in resultados:
        nome = p.get("title", "")
        criador = p.get("user", {}).get("name", "")
        if pais.lower() in nome.lower():
            candidatas.append(p)

    # Prioriza playlists criadas pelo próprio Deezer
    oficiais = [p for p in candidatas if p.get("user", {}).get("name", "").lower() == "deezer"]
    if len(oficiais) == 1:
        return oficiais[0]

    print(f"\n--- Múltiplas opções para '{pais}', escolha manualmente ---")
    lista = oficiais if oficiais else candidatas
    for i, p in enumerate(lista):
        print(f"[{i}] id={p['id']} | título='{p['title']}' | criador='{p.get('user', {}).get('name')}' | faixas={p.get('nb_tracks')}")

    if not lista:
        print(f"Nenhuma playlist encontrada para {pais}. Tente buscar manualmente no site do Deezer.")
        return None

    idx = int(input("Digite o índice da playlist correta: "))
    return lista[idx]


def buscar_faixas_playlist(playlist_id):
    """Retorna todas as faixas de uma playlist, seguindo paginação se houver."""
    faixas = []
    url = f"{BASE_URL}/playlist/{playlist_id}/tracks"
    params = {"limit": 100}

    while url:
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        payload = resp.json()
        faixas.extend(payload.get("data", []))
        url = payload.get("next")  # Deezer já devolve a próxima URL pronta
        params = {}  # os parâmetros já vêm embutidos na URL 'next'
        time.sleep(0.2)  # gentileza com o rate limit (50 req / 5s)

    return faixas


def main():
    linhas_saida = []

    for pais in PAISES:
        print(f"\n=== Buscando playlist Top {pais} ===")
        resultados = buscar_playlist(pais)
        playlist = escolher_playlist_oficial(resultados, pais)

        if playlist is None:
            continue

        print(f"Playlist escolhida: '{playlist['title']}' (id={playlist['id']}, {playlist.get('nb_tracks')} faixas)")
        faixas = buscar_faixas_playlist(playlist["id"])
        print(f"Faixas obtidas: {len(faixas)}")

        for posicao, faixa in enumerate(faixas, start=1):
            linhas_saida.append({
                "pais": pais,
                "posicao": posicao,
                "track_id": faixa.get("id"),
                "titulo": faixa.get("title"),
                "artista": faixa.get("artist", {}).get("name"),
                "album": faixa.get("album", {}).get("title"),
                "duration_seg": faixa.get("duration"),
                "rank": faixa.get("rank"),
                # Preencha manualmente depois de revisar:
                "e_brasileira": "",
                "genero_estimado": "",
            })

        time.sleep(0.5)

    # Salva tudo em um único CSV para checagem manual no Excel/Sheets
    campos = ["pais", "posicao", "track_id", "titulo", "artista", "album",
              "duration_seg", "rank", "e_brasileira", "genero_estimado"]

    with open("top_paises_bruto.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(linhas_saida)

    print(f"\nConcluído! {len(linhas_saida)} faixas salvas em 'top_paises_bruto.csv'.")
    print("Abra o CSV e preencha manualmente as colunas 'e_brasileira' (sim/nao)")
    print("e 'genero_estimado' (ex: sertanejo, funk, mpb, pop, axe...) para as que forem.")


if __name__ == "__main__":
    main()