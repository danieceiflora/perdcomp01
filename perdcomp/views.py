from django.shortcuts import render
from django.http import JsonResponse
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from datetime import datetime
import json


def token_jwt_view(request):
    return render(request, 'token_jwt.html')


def selic_acumulada_view(request):
    """API interna para acumular a SELIC no intervalo informado.

    Query params:
      - dataInicial: str no formato dd/mm/aaaa (obrigatório)
      - dataFinal: str no formato dd/mm/aaaa (obrigatório)
      - codigo_serie: int opcional (padrão 4390 = SELIC acumulada no mês)

    Retorno JSON:
      {
        "codigo_serie": 4390,
        "data_inicial": "01/01/2023",
        "data_final": "31/12/2023",
        "quantidade_registros": 12,
        "soma": "0.123456",            # soma simples dos valores
        "acumulado_composto": "0.131234", # (prod(1+v) - 1)
        "fonte": "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo_serie}/dados?..."
      }
    """
    data_inicial = request.GET.get("dataInicial")
    data_final = request.GET.get("dataFinal")
    codigo_serie = request.GET.get("codigo_serie", "4390")
    # Quando percent=1 (padrão), interpretamos os valores retornados como porcentagem e convertemos para fração dividindo por 100
    percent_flag = request.GET.get("percent", "1") in ("1", "true", "True")

    if not data_inicial or not data_final:
        return JsonResponse(
            {"detail": "Parâmetros obrigatórios: dataInicial e dataFinal (formato dd/mm/aaaa)."},
            status=400,
        )

    # Valida formato de data dd/mm/aaaa
    try:
        di = datetime.strptime(data_inicial, "%d/%m/%Y").date()
        df = datetime.strptime(data_final, "%d/%m/%Y").date()
        if df < di:
            return JsonResponse({"detail": "dataFinal deve ser maior ou igual a dataInicial."}, status=400)
    except ValueError:
        return JsonResponse({"detail": "Datas inválidas. Use dd/mm/aaaa."}, status=400)

    # Monta URL da API do BCB
    try:
        int(codigo_serie)
    except ValueError:
        return JsonResponse({"detail": "codigo_serie deve ser inteiro."}, status=400)

    base_url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo_serie}/dados"
    query = urlencode({
        "formato": "json",
        "dataInicial": data_inicial,
        "dataFinal": data_final,
    })
    url = f"{base_url}?{query}"

    try:
        req = Request(url, headers={"User-Agent": "perdcomp/selic-acumulada"})
        with urlopen(req, timeout=15) as resp:
            if resp.status != 200:
                return JsonResponse({"detail": f"BCB retornou status {resp.status}."}, status=502)
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        return JsonResponse({"detail": f"Falha ao consultar BCB: {exc}"}, status=502)

    # Espera-se uma lista de objetos {"data": "dd/mm/aaaa", "valor": "0.01234"}
    # A série 4390 (SELIC acumulada no mês) costuma repetir o mesmo valor em diversos dias do mês.
    # Para evitar sobrecontagem, agregamos por mês/ano e pegamos o último dia disponível de cada mês.
    por_mes = {}
    for item in data or []:
        try:
            d = datetime.strptime(item.get("data", ""), "%d/%m/%Y").date()
        except Exception:
            continue
        if d < di or d > df:
            continue
        chave = (d.year, d.month)
        atual = por_mes.get(chave)
        if not atual or d > atual["data"]:
            # guarda último dia encontrado no mês
            try:
                v = Decimal(str(item.get("valor")))
            except (InvalidOperation, TypeError):
                continue
            # Interpretação de escala
            if percent_flag:
                # trata sempre como porcentagem -> fração
                v = v / Decimal("100")
            else:
                # heurística: se for claramente > 1, assume porcentagem e divide
                if v > 1:
                    v = v / Decimal("100")
            por_mes[chave] = {"data": d, "valor": v}

    # Agora acumulamos apenas um valor por mês
    meses_ordenados = sorted(por_mes.keys())
    total_soma = Decimal("0")
    total_composto = Decimal("1")
    for chave in meses_ordenados:
        v = por_mes[chave]["valor"]
        total_soma += v
        total_composto *= (Decimal("1") + v)

    quantidade_meses = len(meses_ordenados)
    acumulado_composto = (total_composto - Decimal("1")) if quantidade_meses > 0 else Decimal("0")

    # Evita notação científica no JSON
    def dec_to_str(x: Decimal, places: int = 12) -> str:
        try:
            q = Decimal(1).scaleb(-places)  # 10^-places
            return format(x.quantize(q, rounding=ROUND_HALF_UP), 'f').rstrip('0').rstrip('.') if '.' in format(x.quantize(q, rounding=ROUND_HALF_UP), 'f') else format(x.quantize(q, rounding=ROUND_HALF_UP), 'f')
        except Exception:
            s = format(x, 'f')
            return s

    return JsonResponse(
        {
            "codigo_serie": int(codigo_serie),
            "data_inicial": data_inicial,
            "data_final": data_final,
            "quantidade_meses": quantidade_meses,
            "soma_mensal": dec_to_str(total_soma),          # fração (ex.: 0.12 = 12%)
            "acumulado_composto": dec_to_str(acumulado_composto),  # fração (ex.: 0.15 = 15%)
            "interpretacao": "percent" if percent_flag else "auto",
            "fonte": url,
        }
    )
