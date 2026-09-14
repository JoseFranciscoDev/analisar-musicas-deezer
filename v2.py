"""
Coleta de dados de playlists da API pública do Deezer.

Para cada playlist informada, busca:
    - nome_da_musica
    - nome_do_autor (artista)
    - genero_musical
    - popularidade_estim  (proxy de "visualizacoes", ver observacao abaixo)
    - pais_editorial      (associado manualmente por voce, ver observacao abaixo)

OBSERVACOES IMPORTANTES SOBRE OS CAMPOS:

1) "Visualizacoes":
   A API do Deezer NAO retorna numero de visualizacoes/plays de faixas.
   O campo mais proximo disponivel no endpoint /playlist/{id} e o "rank"
   de cada faixa, que e uma metrica interna de popularidade do Deezer
   (quanto maior, mais popular). Uso esse campo como proxy, deixando
   isso explicito na coluna "popularidade_estim_rank".

2) "Genero":
   O endpoint /playlist/{id} NAO traz genero por faixa. O genero so
   existe associado a ALBUM (endpoint /album/{id}, campo "genres") ou
   a genero editorial (/genre). Por isso, para cada faixa, o script
   faz uma segunda chamada em /album/{album_id} para buscar o genero
   do album ao qual a faixa pertence. Isso deixa a coleta mais lenta
   (1 chamada extra por faixa), mas e a unica forma confiavel.

3) "Editora do pais" / pais associado a playlist:
   A API do Deezer NAO informa a qual pais uma playlist pertence
   (isso so existe para playlists editoriais oficiais, via
   /editorial/{id_pais}/charts). Para uma playlist qualquer (como a
   1116189381), esse dado nao existe no retorno da API. Por isso,
   o pais e um valor que VOCE informa manualmente ao cadastrar a
   playlist na lista de entrada (variavel PAIS_ASSOCIADO_PLAYLIST).

Estrutura pensada para ser facilmente expansivel: basta adicionar mais
playlists (id + pais) na lista de entrada, ou digitar novos IDs quando
o script perguntar interativamente.
"""

import csv
import time

import requests

URL_BASE_API_DEEZER = "https://api.deezer.com"

# Cache simples para nao buscar o mesmo album mais de uma vez
# (varias faixas de uma playlist podem vir do mesmo album)
cache_genero_por_album = {}


def buscar_genero_do_album(id_do_album):
    """
    Busca o genero musical de um album na API do Deezer.
    Retorna o nome do primeiro genero encontrado, ou 'Genero nao informado'
    caso o album nao tenha genero cadastrado.
    """
    if id_do_album in cache_genero_por_album:
        return cache_genero_por_album[id_do_album]

    url_album = f"{URL_BASE_API_DEEZER}/album/{id_do_album}"
    resposta_album = requests.get(url_album)
    dados_album = resposta_album.json()

    lista_generos = dados_album.get("genres", {}).get("data", [])
    if lista_generos:
        nome_genero = lista_generos[0].get("name", "Genero nao informado")
    else:
        nome_genero = "Genero nao informado"

    cache_genero_por_album[id_do_album] = nome_genero
    return nome_genero


def coletar_faixas_da_playlist(id_da_playlist, pais_associado_playlist):
    """
    Busca todas as faixas de uma playlist do Deezer e monta uma lista
    de dicionarios com os dados de interesse de cada faixa.
    """
    url_playlist = f"{URL_BASE_API_DEEZER}/playlist/{id_da_playlist}"
    resposta_playlist = requests.get(url_playlist)
    dados_playlist = resposta_playlist.json()

    if "error" in dados_playlist:
        print(
            f"  Erro ao buscar playlist {id_da_playlist}: {dados_playlist['error'].get('message')}"
        )
        return []

    nome_da_playlist = dados_playlist.get("title", "Titulo desconhecido")
    lista_de_faixas = dados_playlist.get("tracks", {}).get("data", [])

    print(f"  Playlist: {nome_da_playlist} | {len(lista_de_faixas)} faixas encontradas")

    dados_coletados = []

    for faixa in lista_de_faixas:
        nome_da_musica = faixa.get("title")
        nome_do_autor = faixa.get("artist", {}).get("name")
        id_do_album = faixa.get("album", {}).get("id")
        popularidade_estim_rank = faixa.get("rank")

        genero_musical = (
            buscar_genero_do_album(id_do_album) if id_do_album else "Genero nao informado"
        )

        dados_coletados.append(
            {
                "id_playlist": id_da_playlist,
                "nome_playlist": nome_da_playlist,
                "pais_associado_playlist": pais_associado_playlist,
                "nome_da_musica": nome_da_musica,
                "nome_do_autor": nome_do_autor,
                "genero_musical": genero_musical,
                "popularidade_estim_rank": popularidade_estim_rank,
            }
        )

        # pequena pausa para nao sobrecarregar a API publica
        time.sleep(0.1)

    return dados_coletados


def perguntar_lista_de_playlists():
    """
    Pergunta ao usuario, em loop, quais playlists (id + pais associado)
    ele quer incluir na coleta. Digite vazio no ID para encerrar.
    """
    playlists_informadas = []

    print("Informe as playlists que deseja coletar.")
    print("(pressione Enter sem digitar nada no ID para finalizar a lista)\n")

    while True:
        id_da_playlist = input("ID da playlist: ").strip()
        if id_da_playlist == "":
            break

        pais_associado_playlist = input(
            "Pais associado a essa playlist (ou Enter para deixar em branco): "
        ).strip()
        if pais_associado_playlist == "":
            pais_associado_playlist = "Nao informado"

        playlists_informadas.append(
            {
                "id_da_playlist": id_da_playlist,
                "pais_associado_playlist": pais_associado_playlist,
            }
        )
        print()

    return playlists_informadas


def salvar_resultados_em_csv(
    todos_os_dados_coletados, caminho_do_arquivo="dados_playlists_deezer.csv"
):
    """
    Salva a lista de dicionarios coletados em um arquivo CSV.
    """
    if not todos_os_dados_coletados:
        print("Nenhum dado para salvar.")
        return

    colunas = todos_os_dados_coletados[0].keys()

    with open(caminho_do_arquivo, mode="w", newline="", encoding="utf-8") as arquivo_csv:
        escritor_csv = csv.DictWriter(
            arquivo_csv,
            fieldnames=colunas,
            delimiter=";",
        )
        escritor_csv.writeheader()
        escritor_csv.writerows(todos_os_dados_coletados)

    print(f"\nDados salvos em: {caminho_do_arquivo}")


def main():
    # Playlist inicial ja definida pelo usuario.
    # PAIS_ASSOCIADO_PLAYLIST: como a API nao informa o pais de uma
    playlists_para_coletar = [
        {"id_da_playlist": "1111141961", "pais_associado_playlist": "Top músicas Brasil"},  # brasil
        {"id_da_playlist": "1109890291", "pais_associado_playlist": "Top músicas França"},  # franca
        {"id_da_playlist": "1111142361", "pais_associado_playlist": "Top músicas México"},
        {"id_da_playlist": "1111143121", "pais_associado_playlist": "Top músicas Alemanha"},
        {"id_da_playlist": "1313621735", "pais_associado_playlist": "Top músicas Estados unidos"},
    ]

    print("=== Coleta de dados de playlists - API Deezer ===\n")

    resposta_usuario = input("Deseja adicionar mais playlists agora? (s/n): ").strip().lower()
    if resposta_usuario == "s":
        playlists_para_coletar.extend(perguntar_lista_de_playlists())

    todos_os_dados_coletados = []

    for playlist in playlists_para_coletar:
        print(f"\nColetando playlist {playlist['id_da_playlist']}...")
        dados_da_playlist = coletar_faixas_da_playlist(
            id_da_playlist=playlist["id_da_playlist"],
            pais_associado_playlist=playlist["pais_associado_playlist"],
        )
        todos_os_dados_coletados.extend(dados_da_playlist)

    salvar_resultados_em_csv(todos_os_dados_coletados)


main()
