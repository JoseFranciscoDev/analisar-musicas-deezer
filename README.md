# Coleta de dados de playlists da API pública do Deezer.

## Para cada playlist informada, busca:
    - nome_da_musica
    - nome_do_autor (artista)
    - genero_musical
    - popularidade_estim  (proxy de "visualizacoes", ver observacao abaixo)
    - pais_editorial      (associado manualmente por voce, ver observacao abaixo)

##  OBSERVACOES IMPORTANTES SOBRE OS CAMPOS:

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