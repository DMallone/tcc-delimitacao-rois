# ================================================================
# TCC - Delimitacao manual das Regioes de Interesse (ROIs)
# ================================================================

# Bibliotecas utilizadas:
# json: grava coordenadas e metadados em um arquivo JSON.
# pathlib.Path: organiza os caminhos dos arquivos de forma portavel.
# cv2 (OpenCV): carrega a imagem, permite selecionar ROIs e gera a previa.
import json
from pathlib import Path
import cv2

# 1. DEFINICAO DOS ARQUIVOS E PARAMETROS

# BASE indica a pasta onde este script esta salvo.
# Os demais caminhos sao definidos em relacao a essa pasta.
BASE = Path(__file__).resolve().parent

# Imagem previamente extraida do video, usada para selecionar as bancadas.
IMAGEM = BASE / 'resultados' / 'frame_33min.png'

# Caminho do video original, armazenado apenas como informacao no JSON.
VIDEO = BASE / 'videos' / 'gravacao_33min_h264.mp4'

# Arquivo que o programa de monitoramento utilizara para ler as ROIs.
# O nome "15min" foi mantido para preservar os caminhos do experimento.
SAIDA_JSON = BASE / 'resultados' / 'rois_bancadas_15min.json'

# Imagem de conferencia com os retangulos e rotulos das bancadas.
SAIDA_PREVIEW = BASE / 'resultados' / 'rois_bancadas_15min_preview.png'

# Largura exibida na tela durante a selecao manual.
# As coordenadas serao corrigidas posteriormente para a resolucao original.
LARGURA_EXIBICAO = 960

# 2. LEITURA E REDIMENSIONAMENTO DA IMAGEM

# Carrega a imagem; o script para se ela nao estiver no caminho indicado.
imagem = cv2.imread(str(IMAGEM))
if imagem is None:
    raise FileNotFoundError(f'Imagem nao encontrada ou invalida: {IMAGEM}')

# Obtém a resolucao original: altura e largura, em pixels.
altura_original, largura_original = imagem.shape[:2]

# Calcula uma altura proporcional para evitar deformar a imagem.
altura_exibicao = round(altura_original * LARGURA_EXIBICAO / largura_original)

# Gera a versao reduzida da imagem, facilitando o uso do mouse.
menor = cv2.resize(imagem, (LARGURA_EXIBICAO, altura_exibicao), interpolation=cv2.INTER_AREA)

# Fatores de conversao para retornar as coordenadas da janela reduzida
# a resolucao original, nos eixos horizontal (fx) e vertical (fy).
fx, fy = largura_original / LARGURA_EXIBICAO, altura_original / altura_exibicao
print(f'Imagem original: {largura_original}x{altura_original}')
print(f'Selecao em: {LARGURA_EXIBICAO}x{altura_exibicao}; escala X={fx:.4f}, Y={fy:.4f}')

# 3. SELECAO MANUAL DAS REGIOES DE INTERESSE (ROIs)

# Abre uma janela interativa: o usuario desenha um retangulo para cada
# bancada, confirma com ENTER e encerra com ESC.
# Cada retangulo retorna (x, y, largura, altura) na imagem reduzida.
print('Desenhe cada bancada e confirme com ENTER. ESC finaliza.')
selecoes = cv2.selectROIs('Bancadas - visualizacao reduzida', menor, showCrosshair=True, fromCenter=False)
cv2.destroyAllWindows()

# Se nao houver selecoes, o script termina sem alterar os arquivos existentes.
if len(selecoes) == 0:
    print('Nenhuma ROI selecionada. Arquivos anteriores preservados.')
    raise SystemExit(0)

# 4. CORRECAO DAS COORDENADAS E IDENTIFICACAO DAS BANCADAS

# Faz uma copia da imagem original para desenhar as ROIs sem alterar
# a imagem de referencia carregada.
preview = imagem.copy()

# Lista de regioes que sera gravada no arquivo JSON.
rois = []
for n, (x, y, w, h) in enumerate(selecoes, 1):
    # Desconsidera selecoes que nao formam um retangulo valido.
    if w <= 0 or h <= 0:
        continue

    # Converte o canto superior esquerdo e o inferior direito do
    # retangulo para as coordenadas da resolucao original.
    x1 = round(x * fx)
    y1 = round(y * fy)
    x2 = min(largura_original, round((x + w) * fx))
    y2 = min(altura_original, round((y + h) * fy))

    # Armazena o numero, o nome e a geometria original de cada bancada.
    # x/y = inicio do retangulo; w/h = largura/altura, em pixels.
    rois.append(dict(id=n, nome=f'bancada_{n}', x=x1, y=y1, w=x2 - x1, h=y2 - y1))

    # Marca as ROIs em verde e escreve B1, B2... na imagem de conferencia.
    cv2.rectangle(preview, (x1, y1), (x2, y2), (0, 255, 0), 3)
    cv2.putText(preview, f'B{n}', (x1, max(26, y1 - 9)), cv2.FONT_HERSHEY_SIMPLEX, .8, (0, 255, 0), 2)

# Evita criar arquivos de saida caso nenhuma ROI valida tenha sido definida.
if not rois:
    raise RuntimeError('Nenhuma ROI valida selecionada.')

# 5. SALVAMENTO DA IMAGEM E DAS COORDENADAS

# Cria a pasta de resultados, caso ela ainda nao exista.
SAIDA_JSON.parent.mkdir(parents=True, exist_ok=True)

# Salva a imagem com as bancadas para conferencia visual.
if not cv2.imwrite(str(SAIDA_PREVIEW), preview):
    raise RuntimeError(f'Falha ao salvar: {SAIDA_PREVIEW}')

# Prepara os metadados e as coordenadas das ROIs.
# A lista "rois" e utilizada posteriormente pelo script de monitoramento.
config = dict(video_base=str(VIDEO), imagem_referencia=str(IMAGEM), largura_video=largura_original, altura_video=altura_original, rois=rois)

# Grava o JSON de forma legivel, preservando caracteres em UTF-8.
with SAIDA_JSON.open('w', encoding='utf-8') as f:
    json.dump(config, f, indent=4, ensure_ascii=False)

# 6. CONFIRMACAO DOS ARQUIVOS GERADOS

# Exibe o numero de regioes selecionadas e onde cada arquivo foi salvo.
print('ROIs:', len(rois))
print('JSON:', SAIDA_JSON)
print('Preview:', SAIDA_PREVIEW)