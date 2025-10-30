import re
from decimal import Decimal, InvalidOperation
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List


def _parse_ptbr_number(s: str) -> Optional[Decimal]:
    if not s:
        return None
    s = s.strip()
    s = s.replace(".", "").replace(",", ".")
    try:
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return None


def _clean_cnpj(s: str) -> str:
    if not s:
        return ""
    return re.sub(r"[^0-9]", "", s)


def _looks_like_perdcomp(value: str | None) -> bool:
    if not value:
        return False
    candidate = value.strip()
    if len(candidate) < 12:
        return False
    if '/' in candidate:
        return False
    if candidate.lower().startswith('perdcomp'):
        return False
    if re.fullmatch(r"\d+\.\d{1,2}", candidate):
        return False
    separator_count = sum(ch in '.-' for ch in candidate)
    if separator_count < 2:
        return False
    return bool(re.search(r"\d", candidate)) and any(ch in candidate for ch in ('.', '-'))


def _find_perdcomp_candidate(text: str, exclude: Optional[List[str]] = None) -> Optional[str]:
    if not text:
        return None
    excluded = {val.strip() for val in (exclude or []) if val}
    search_scope = text
    patterns = (
        r"\b\d{5,}\.\d{4,}\.\d{5,}\.\d\.\d\.\d{2}-\d{4}\b",
        r"\b\d[\d.\-]{11,}\d\b",
    )
    for pattern in patterns:
        for match in re.finditer(pattern, search_scope):
            candidate = match.group(0).strip()
            if excluded and candidate in excluded:
                continue
            if _looks_like_perdcomp(candidate):
                return candidate
    for loose_match in re.finditer(r"\d[\d.\-\s]{11,}\d", search_scope):
        candidate = re.sub(r"\s+", "", loose_match.group(0)).strip(" .;,:")
        if excluded and candidate in excluded:
            continue
        if _looks_like_perdcomp(candidate):
            return candidate
    return None


@dataclass
class PDFParsed:
    cnpj: Optional[str] = None
    perdcomp: Optional[str] = None
    perdcomp_inicial: Optional[str] = None
    perdcomp_retificador: Optional[str] = None
    is_retificador: bool = False
    metodo_credito: Optional[str] = None
    data_criacao: Optional[str] = None  # dd/mm/aaaa
    valor_pedido: Optional[Decimal] = None
    ano: Optional[str] = None
    trimestre: Optional[str] = None  # 1..4
    tipo_credito: Optional[str] = None
    # Campos específicos (principalmente usados em Pedido de restituição)
    data_arrecadacao: Optional[str] = None  # dd/mm/aaaa
    periodo_apuracao_credito: Optional[str] = None  # mm/aaaa
    codigo_receita: Optional[str] = None
    # Débitos extraídos de Declaração de Compensação / documentos vinculados
    # Cada item: {
    #   'item': str | None,
    #   'codigo_receita_denominacao': str | None,
    #   'periodo_apuracao_debito': str | None,
    #   'valor': Decimal | None,
    # }
    debitos: List[Dict[str, Any]] = field(default_factory=list)
    # Valor Total na seção 'Origem do Crédito' (usado como saldo do crédito)
    valor_total_origem: Optional[Decimal] = None
    # Valor Original do Crédito Inicial (bloco 'CRÉDITO PAGAMENTO INDEVIDO OU A MAIOR' ou similar)
    valor_original_credito_inicial: Optional[Decimal] = None
    # Total dos Débitos deste Documento (soma dos débitos compensados)
    total_debitos_documento: Optional[Decimal] = None
    # Total do Crédito Original Utilizado neste Documento
    total_credito_original_utilizado: Optional[Decimal] = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            'cnpj': self.cnpj,
            'perdcomp': self.perdcomp,
            'metodo_credito': self.metodo_credito,
            'data_criacao': self.data_criacao,
            'valor_pedido': str(self.valor_pedido) if self.valor_pedido is not None else None,
            'ano': self.ano,
            'trimestre': self.trimestre,
            'tipo_credito': self.tipo_credito,
            'data_arrecadacao': self.data_arrecadacao,
            'periodo_apuracao_credito': self.periodo_apuracao_credito,
            'codigo_receita': self.codigo_receita,
            'perdcomp_inicial': self.perdcomp_inicial,
            'perdcomp_retificador': self.perdcomp_retificador,
            'is_retificador': self.is_retificador,
        }


def parse_ressarcimento_text(txt: str) -> PDFParsed:
    """
    Extrai campos de um texto de PERDCOMP (Ressarcimento/Restituição/Compensação).
    Espera rótulos como: CNPJ, PERDCOMP, Tipo de Documento, Data de Criação,
    Valor do Pedido de Ressarcimento, Ano, Trimestre, Tipo de Crédito.
    """
    p = PDFParsed()
    if not txt:
        return p

    # Normalizar quebras e espaços múltiplos para facilitar regex com DOTALL minimalista
    norm = re.sub(r"[\t\u00A0]+", " ", txt)

    # ETAPA 1: Número do PER/DCOMP inicial (seção "Nº do PER/DCOMP inicial")
    # Este é o número que identifica a adesão original e deve ser capturado PRIMEIRO
    m_initial = re.search(
        r"N[ºo°]\s*do\s+PER\s*/?\s*DCOMP\s+(?:inicial|a\s+ser\s+retificad[ao]|original)\s*[:\-]?\s*([0-9A-Za-z./\-\s]+)",
        norm,
        flags=re.IGNORECASE,
    )
    if not m_initial:
        m_initial = re.search(
            r"PER\s*/?\s*DCOMP\s+(?:a\s+ser\s+retificad[ao]|original)\s*[:\-]?\s*([0-9A-Za-z./\-\s]+)",
            norm,
            flags=re.IGNORECASE,
        )
    if m_initial:
        raw_initial = m_initial.group(1).strip()
        # Remove letras e mantém apenas números, pontos, traços e barras
        candidate_initial = re.sub(r"[^0-9.\-/]", "", raw_initial)
        candidate_initial = candidate_initial.strip(" .;,:")
        if _looks_like_perdcomp(candidate_initial):
            p.perdcomp_inicial = candidate_initial
        else:
            # Procurar nas proximidades do label
            search_tail = (raw_initial + " " + norm[m_initial.end(): m_initial.end() + 200]).strip()
            candidate_initial = _find_perdcomp_candidate(search_tail)
            if not candidate_initial:
                candidate_initial = _find_perdcomp_candidate(norm[m_initial.end(): m_initial.end() + 200])
            if candidate_initial:
                p.perdcomp_inicial = candidate_initial

    # ETAPA 2: Capturar CNPJ e o PERDCOMP do cabeçalho (número da declaração atual)
    # Este número aparece no topo do documento, geralmente destacado, e é o número desta declaração
    m_cnpj = re.search(r"CNPJ\s*[:\-]?\s*([0-9./-]{14,20})", norm, flags=re.IGNORECASE)
    if m_cnpj:
        p.cnpj = _clean_cnpj(m_cnpj.group(1))
        # O número que aparece após CNPJ (geralmente destacado) é o PERDCOMP da declaração
        tail_segment = norm[m_cnpj.end(): m_cnpj.end() + 120]
        m_after = re.match(r"\s*([0-9A-Za-z./\-]+)", tail_segment)
        if m_after:
            candidate = m_after.group(1).strip().strip(" .;,:")
            # Este é o PERDCOMP da DECLARAÇÃO (diferente do inicial)
            if _looks_like_perdcomp(candidate) and candidate != p.perdcomp_inicial:
                p.perdcomp = candidate
        if not p.perdcomp:
            candidate = _find_perdcomp_candidate(tail_segment, [p.perdcomp_inicial])
            if candidate:
                p.perdcomp = candidate
        if not p.perdcomp:
            head_segment = norm[max(0, m_cnpj.start() - 120): m_cnpj.start()]
            candidate = _find_perdcomp_candidate(head_segment, [p.perdcomp_inicial])
            if candidate:
                p.perdcomp = candidate

    # ETAPA 3: Fallbacks adicionais para capturar número da declaração
    if not p.perdcomp:
        m_per = re.search(r"PER\s*/?\s*DCOMP(?!\s*inicial)\s*(?:n[ºo]\s*)?[:\-]?\s*([0-9A-Za-z.\-]+)", norm, flags=re.IGNORECASE)
        if m_per:
            candidate = m_per.group(1).strip()
            if _looks_like_perdcomp(candidate) and candidate != p.perdcomp_inicial:
                p.perdcomp = candidate

    if not p.perdcomp:
        m_decl = re.search(r"Declara[cç][aã]o\s+de\s+Compensa[cç][aã]o\s*(?:n[ºo]\s*)?[:\-]?\s*([0-9A-Za-z.\-]+)", norm, flags=re.IGNORECASE)
        if m_decl:
            candidate = m_decl.group(1).strip()
            if _looks_like_perdcomp(candidate) and candidate != p.perdcomp_inicial:
                p.perdcomp = candidate

    if not p.perdcomp:
        candidate = _find_perdcomp_candidate(norm, [p.perdcomp_inicial])
        if candidate:
            p.perdcomp = candidate

    # ETAPA 4: Último fallback - usar inicial apenas se realmente não encontrou nada
    # (isso só deve acontecer em PDFs de adesão inicial, não em declarações)
    if not p.perdcomp and p.perdcomp_inicial:
        p.perdcomp = p.perdcomp_inicial

    # Identifica se o documento é retificador
    if p.perdcomp_inicial and p.perdcomp and p.perdcomp != p.perdcomp_inicial:
        p.is_retificador = True
        p.perdcomp_retificador = p.perdcomp
    elif re.search(r"\bretificador(?:a)?\b", norm, flags=re.IGNORECASE):
        p.is_retificador = True
        if p.perdcomp and not p.perdcomp_retificador:
            p.perdcomp_retificador = p.perdcomp

    # Tipo de Documento -> mapeia para metodo_credito conforme opções do sistema
    m = re.search(r"Tipo de Documento\s*[:\-]?\s*(.+)", norm, flags=re.IGNORECASE)
    if m:
        raw = m.group(1).strip()
        # Heurística simples para mapear para choices
        low = raw.lower()
        if 'ressarc' in low:
            p.metodo_credito = 'Pedido de ressarcimento'
        elif 'restitui' in low:
            p.metodo_credito = 'Pedido de restituição'
        elif 'declara' in low and 'compensa' in low:
            # Declaração de Compensação: detectar vinculação se constar no texto completo
            # Heurística: procurar frases de vinculação em todo o documento
            whole_low = norm.lower()
            if 'vinculada a um pedido de restitui' in whole_low:
                p.metodo_credito = 'Compensação vinculada a um pedido de restituição'
            elif 'vinculada a um pedido de ressarc' in whole_low:
                p.metodo_credito = 'Compensação vinculada a um pedido de ressarcimento'
            else:
                # Documento genérico de Declaração de Compensação (sem vínculo direto)
                p.metodo_credito = 'Declaração de Compensação'
        else:
            p.metodo_credito = raw

    # Data de Criação dd/mm/aaaa
    m = re.search(r"Data de Cria[cç][aã]o\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})", norm, flags=re.IGNORECASE)
    if m:
        p.data_criacao = m.group(1)

    # Data de Arrecadação dd/mm/aaaa (para Pedido de restituição)
    m = re.search(r"Data de Arrecada[cç][aã]o\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})", norm, flags=re.IGNORECASE)
    if m:
        p.data_arrecadacao = m.group(1)

    # Valor do Pedido (Ressarcimento/Restituição)
    m = re.search(r"Valor do Pedido.*?([0-9.]+,\d{2})", norm, flags=re.IGNORECASE | re.DOTALL)
    if m:
        p.valor_pedido = _parse_ptbr_number(m.group(1))

    # Período de Apuração (Crédito): pode vir como dd/mm/aaaa (ex.: 30/06/2020) ou mm/aaaa.
    # 1) Captura direta com dd/mm/aaaa
    m = re.search(r"(?:\b\d+\s*\.\s*)?Per[ií]odo\s+de\s+Apura[cç][aã]o\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})", norm, flags=re.IGNORECASE)
    if m:
        # Manter como aparece no PDF (dd/mm/aaaa)
        p.periodo_apuracao_credito = m.group(1)
    else:
        # 2) Captura direta com mm/aaaa
        m = re.search(r"(?:\b\d+\s*\.\s*)?Per[ií]odo\s+de\s+Apura[cç][aã]o\s*[:\-]?\s*(\d{2}/\d{4})", norm, flags=re.IGNORECASE)
        if m:
            p.periodo_apuracao_credito = m.group(1)
        else:
            # 3) Fallback: encontra o rótulo e procura a primeira data próxima em até ~120 caracteres
            label = re.search(r"(?:\b\d+\s*\.\s*)?Per[ií]odo\s+de\s+Apura[cç][aã]o", norm, flags=re.IGNORECASE)
            if label:
                tail = norm[label.end():label.end() + 200]
                m = re.search(r"(\d{2}/\d{2}/\d{4}|\d{2}/\d{4})", tail)
                if m:
                    p.periodo_apuracao_credito = m.group(1)

    # Código da Receita
    m = re.search(r"C[oó]digo (?:da|de) Receita\s*[:\-]?\s*([0-9.]+)", norm, flags=re.IGNORECASE)
    if m:
        p.codigo_receita = m.group(1).strip()

    # Ano
    m = re.search(r"\bAno\b\s*[:\-]?\s*(\d{4})", norm, flags=re.IGNORECASE)
    if m:
        p.ano = m.group(1)

    # Trimestre (e.g., 1º Trimestre)
    m = re.search(r"(\d+)\s*º?\s*Trimestre", norm, flags=re.IGNORECASE)
    if m:
        p.trimestre = m.group(1)

    # Tipo de Crédito
    m = re.search(r"Tipo de Cr[eé]dito\s*[:\-]?\s*(.+)", norm, flags=re.IGNORECASE)
    if m:
        p.tipo_credito = m.group(1).strip()

    # Extração de múltiplos Débitos em 'Declaração de Compensação'
    # Busca blocos iniciando com número e a palavra Débito
    debitos: List[Dict[str, Any]] = []
    for blk in re.finditer(r"(?ms)^\s*(\d{1,3})\s*\.\s*D[eé]bito\s*(.*?)(?=^\s*\d{1,3}\s*\.\s*D[eé]bito|\Z)", norm):
        block = blk.group(0)
        item_number = blk.group(1).strip() if blk.group(1) else None
        if item_number:
            item_number = item_number.zfill(3)
        # Tenta obter um título do débito a partir da primeira linha
        titulo = None
        mtitle = re.search(r"^\s*\d{1,3}\s*\.\s*D[eé]bito\s*(.*?)\s*(?:\r?\n|$)", block)
        if mtitle:
            t = mtitle.group(1).strip()
            titulo = t if t else None
        # Código da Receita e Denominação
        cod = None
        denom = None
        mcode = re.search(r"C[oó]digo\s*(?:da|de)\s*Receita\s*[:\-]?\s*([0-9.]+)\s*", block, flags=re.IGNORECASE)
        if mcode:
            cod = mcode.group(1).strip()
        mden = re.search(r"Denomina[cç][aã]o\s*[:\-]?\s*(.+)", block, flags=re.IGNORECASE)
        if mden:
            # Pega até fim de linha
            denom = mden.group(1).strip().splitlines()[0].strip()
        if not denom and (cod or titulo):
            denom = f"{cod or ''} {titulo or ''}".strip()
        # Período de Apuração (Débito)
        per_d = None
        mperd = re.search(r"Per[ií]odo\s+de\s+Apura[cç][aã]o.*?(\d{2}/\d{2}/\d{4}|\d{2}/\d{4})", block, flags=re.IGNORECASE | re.DOTALL)
        if mperd:
            per_d = mperd.group(1)
        # Valor (procurar 'Valor do Débito' ou 'Total')
        val = None
        mval = re.search(r"Valor\s*(?:do\s*D[eé]bito|Total)\s*[:\-]?\s*([0-9.]+,\d{2})", block, flags=re.IGNORECASE)
        if not mval:
            # fallback: primeiro valor monetário no bloco
            mval = re.search(r"([0-9.]+,\d{2})", block)
        if mval:
            val = _parse_ptbr_number(mval.group(1))
        if cod or denom or per_d or val is not None:
            debitos.append({
                'item': item_number,
                'codigo_receita_denominacao': denom or (cod or None),
                'periodo_apuracao_debito': per_d,
                'valor': val,
            })
    if debitos:
        p.debitos = debitos

    # Valor Total na Origem do Crédito
    # Busca o bloco 'ORIGEM DO CRÉDITO' e captura a linha 'Valor Total'
    m_origem = re.search(r"ORIGEM\s+DO\s+CR[EÉ]DITO(.*?)(?=\n\s*[A-Z][A-Z ]{5,}|\Z)", norm, flags=re.IGNORECASE | re.DOTALL)
    if m_origem:
        bloco = m_origem.group(1)
        mv = re.search(r"Valor\s+Total\s*[:\-]?\s*([0-9.]+,\d{2})", bloco, flags=re.IGNORECASE)
        if mv:
            p.valor_total_origem = _parse_ptbr_number(mv.group(1))

    # Valor Original do Crédito Inicial (para documentos sem 'Origem do Crédito')
    # Normalmente aparece no bloco 'CRÉDITO PAGAMENTO INDEVIDO OU A MAIOR'
    m_credito = re.search(r"CR[EÉ]DITO\s+PAGAMENTO\s+INDEVIDO\s+OU\s+A\s+MAIOR(.*?)(?=\n\s*[A-Z][A-Z ]{5,}|\Z)", norm, flags=re.IGNORECASE | re.DOTALL)
    if m_credito:
        bloco_c = m_credito.group(1)
        mvo = re.search(r"Valor\s+Original\s+do\s+Cr[eé]dito\s+Inicial\s*[:\-]?\s*([0-9.]+,\d{2})", bloco_c, flags=re.IGNORECASE)
        if mvo:
            p.valor_original_credito_inicial = _parse_ptbr_number(mvo.group(1))
    # Fallback global: procurar a mesma label no documento todo caso a seção tenha outro título
    if p.valor_original_credito_inicial is None:
        mg = re.search(r"Valor\s+Original\s+do\s+Cr[eé]dito\s+Inicial\s*[:\-]?\s*([0-9.]+,\d{2})", norm, flags=re.IGNORECASE)
        if mg:
            p.valor_original_credito_inicial = _parse_ptbr_number(mg.group(1))

    # Total dos Débitos deste Documento
    m_total_debitos = re.search(
        r"Total\s+dos\s+D[eé]bitos\s+(?:deste\s+Documento|do\s+Documento)?\s*[:\-]?\s*([0-9.]+,\d{2})",
        norm,
        flags=re.IGNORECASE
    )
    if m_total_debitos:
        p.total_debitos_documento = _parse_ptbr_number(m_total_debitos.group(1))
    
    # Total do Crédito Original Utilizado neste Documento
    m_total_credito_utilizado = re.search(
        r"Total\s+(?:do\s+)?Cr[eé]dito\s+Original\s+Utilizado\s+(?:neste\s+Documento|no\s+Documento)?\s*[:\-]?\s*([0-9.]+,\d{2})",
        norm,
        flags=re.IGNORECASE
    )
    if m_total_credito_utilizado:
        p.total_credito_original_utilizado = _parse_ptbr_number(m_total_credito_utilizado.group(1))

    return p


def parse_declaracao_compensacao_text(txt: str) -> PDFParsed:
    """
    Parser específico para DECLARAÇÃO DE COMPENSAÇÃO.
    
    Extrai:
    - perdcomp: Número da declaração atual (aparece no cabeçalho, após CNPJ)
    - perdcomp_inicial: Número do PER/DCOMP inicial (seção "Nº do PER/DCOMP inicial")
    - debitos: Lista de débitos compensados
    - metodo_credito: Sempre "Declaração de Compensação" ou variação vinculada
    - valor_original_credito_inicial: Valor do crédito sendo utilizado
    """
    p = PDFParsed()
    if not txt:
        return p
    
    # Normalizar
    norm = re.sub(r"[\t\u00A0]+", " ", txt)

    # Captura do PER/DCOMP original (quando o documento é retificador)
    m_initial = re.search(
        r"N[ºo°]\s*do\s+PER\s*/?\s*DCOMP\s+(?:inicial|a\s+ser\s+retificad[ao]|original)\s*[:\-]?\s*([0-9A-Za-z./\-\s]+)",
        norm,
        flags=re.IGNORECASE,
    )
    if not m_initial:
        m_initial = re.search(
            r"PER\s*/?\s*DCOMP\s+(?:a\s+ser\s+retificad[ao]|original)\s*[:\-]?\s*([0-9A-Za-z./\-\s]+)",
            norm,
            flags=re.IGNORECASE,
        )
    if m_initial:
        raw_initial = m_initial.group(1).strip()
        candidate_initial = re.sub(r"[^0-9.\-/]", "", raw_initial).strip(" .;,:")
        if _looks_like_perdcomp(candidate_initial):
            p.perdcomp_inicial = candidate_initial
        else:
            tail = norm[m_initial.end():m_initial.end() + 200]
            candidate_initial = _find_perdcomp_candidate(raw_initial + " " + tail)
            if not candidate_initial:
                candidate_initial = _find_perdcomp_candidate(tail)
            if candidate_initial:
                p.perdcomp_inicial = candidate_initial
    
    # 1. CNPJ (obrigatório)
    m_cnpj = re.search(r"CNPJ\s*[:\-]?\s*([0-9./-]{14,20})", norm, flags=re.IGNORECASE)
    if m_cnpj:
        p.cnpj = _clean_cnpj(m_cnpj.group(1))
    
    # 2. Número do PER/DCOMP INICIAL (obrigatório para declaração)
    # Busca explicitamente pela label "Nº do PER/DCOMP inicial"
    m_inicial = re.search(
        r"(?:N[ºo°]\.?\s*do\s+|Nº\s+do\s+|Numero\s+do\s+)?PER\s*/?\s*DCOMP\s+inicial\s*[:\-]?\s*([0-9A-Za-z./\-\s]{15,35})",
        norm,
        flags=re.IGNORECASE
    )
    if m_inicial:
        raw = m_inicial.group(1).strip()
        # Remove espaços e mantém apenas números, pontos, traços e barras
        candidate = re.sub(r"[^0-9.\-/]", "", raw)
        candidate = candidate.strip(" .;,:")
        if _looks_like_perdcomp(candidate):
            p.perdcomp_inicial = candidate
    
    # 3. Número do PERDCOMP da DECLARAÇÃO ATUAL
    # Este número aparece no cabeçalho, geralmente destacado, próximo ao CNPJ
    # É diferente do PER/DCOMP inicial - este identifica a declaração atual
    
    # 3a. Buscar no cabeçalho (linha com PERDCOMP destacado)
    m_header = re.search(
        r"(?:PERDCOMP|PER\s*/?\s*DCOMP)\s+(\d+[\d.\-]+)",
        norm[:500],  # Primeiras linhas do documento
        flags=re.IGNORECASE
    )
    if m_header:
        candidate = m_header.group(1).strip()
        if _looks_like_perdcomp(candidate) and candidate != p.perdcomp_inicial:
            p.perdcomp = candidate
    
    # 3b. Buscar após CNPJ (número geralmente destacado)
    if not p.perdcomp and m_cnpj:
        tail = norm[m_cnpj.end():m_cnpj.end() + 100]
        m_after = re.search(r"(\d{5}[\d.\-]+\d{4})", tail)
        if m_after:
            candidate = m_after.group(1).strip()
            if _looks_like_perdcomp(candidate) and candidate != p.perdcomp_inicial:
                p.perdcomp = candidate
    
    # 3c. Fallback: procurar qualquer PERDCOMP que não seja o inicial
    if not p.perdcomp:
        candidate = _find_perdcomp_candidate(norm, [p.perdcomp_inicial])
        if candidate:
            p.perdcomp = candidate
    
    # 4. Tipo de Documento - confirmar que é Declaração de Compensação
    m_tipo = re.search(r"Tipo\s+de\s+Documento\s*[:\-]?\s*(.+?)(?:\n|$)", norm, flags=re.IGNORECASE)
    if m_tipo:
        tipo_raw = m_tipo.group(1).strip()
        tipo_lower = tipo_raw.lower()
        
        # Detectar se é vinculada
        whole_lower = norm.lower()
        if 'vinculada a um pedido de restitui' in whole_lower or 'vinculad' in tipo_lower and 'restitui' in whole_lower:
            p.metodo_credito = 'Compensação vinculada a um pedido de restituição'
        elif 'vinculada a um pedido de ressarc' in whole_lower or 'vinculad' in tipo_lower and 'ressarc' in whole_lower:
            p.metodo_credito = 'Compensação vinculada a um pedido de ressarcimento'
        else:
            p.metodo_credito = 'Declaração de Compensação'
    else:
        # Default se não encontrar o tipo
        p.metodo_credito = 'Declaração de Compensação'
    
    # 5. Data de Criação
    m_data = re.search(r"Data\s+de\s+Cria[cç][aã]o\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})", norm, flags=re.IGNORECASE)
    if m_data:
        p.data_criacao = m_data.group(1)
    
    # 6. Valor Original do Crédito Inicial (seção CRÉDITO PAGAMENTO INDEVIDO OU A MAIOR)
    m_credito_bloco = re.search(
        r"CR[EÉ]DITO\s+PAGAMENTO\s+INDEVIDO\s+OU\s+A\s+MAIOR(.*?)(?=\n\s*[A-Z][A-Z ]{5,}|\Z)",
        norm,
        flags=re.IGNORECASE | re.DOTALL
    )
    if m_credito_bloco:
        bloco = m_credito_bloco.group(1)
        m_valor = re.search(r"Valor\s+Original\s+do\s+Cr[eé]dito\s+Inicial\s*[:\-]?\s*([0-9.]+,\d{2})", bloco, flags=re.IGNORECASE)
        if m_valor:
            p.valor_original_credito_inicial = _parse_ptbr_number(m_valor.group(1))
    
    # Fallback global
    if p.valor_original_credito_inicial is None:
        m_valor_global = re.search(
            r"Valor\s+Original\s+do\s+Cr[eé]dito\s+Inicial\s*[:\-]?\s*([0-9.]+,\d{2})",
            norm,
            flags=re.IGNORECASE
        )
        if m_valor_global:
            p.valor_original_credito_inicial = _parse_ptbr_number(m_valor_global.group(1))
    
    # 7. DÉBITOS - Extração de múltiplos débitos compensados
    debitos: List[Dict[str, Any]] = []
    
    # Buscar blocos que começam com "N. Débito" onde N é um número
    for match in re.finditer(
        r"(?ms)^\s*(\d{1,3})\s*\.\s*D[eé]bito\s*(.*?)(?=^\s*\d{1,3}\s*\.\s*D[eé]bito|\Z)",
        norm
    ):
        bloco = match.group(0)
        item_num = match.group(1).strip()
        if item_num:
            item_num = item_num.zfill(3)  # 001, 002, etc
        
        # Código da Receita
        codigo = None
        m_cod = re.search(r"C[oó]digo\s*(?:da|de)\s*Receita\s*[:\-]?\s*([0-9.]+)", bloco, flags=re.IGNORECASE)
        if m_cod:
            codigo = m_cod.group(1).strip()
        
        # Denominação
        denominacao = None
        m_denom = re.search(r"Denomina[cç][aã]o\s*[:\-]?\s*(.+?)(?:\n|$)", bloco, flags=re.IGNORECASE)
        if m_denom:
            denominacao = m_denom.group(1).strip().splitlines()[0].strip()
        
        # Se temos código e denominação, juntar
        if codigo and denominacao:
            cod_receita_denom = f"{codigo} - {denominacao}"
        elif codigo:
            cod_receita_denom = codigo
        elif denominacao:
            cod_receita_denom = denominacao
        else:
            cod_receita_denom = None
        
        # Período de Apuração
        periodo = None
        m_per = re.search(
            r"Per[ií]odo\s+de\s+Apura[cç][aã]o.*?(\d{2}/\d{2}/\d{4}|\d{2}/\d{4})",
            bloco,
            flags=re.IGNORECASE | re.DOTALL
        )
        if m_per:
            periodo = m_per.group(1)
        
        # Valor do Débito
        valor = None
        m_val = re.search(
            r"Valor\s*(?:do\s*D[eé]bito|Total)\s*[:\-]?\s*([0-9.]+,\d{2})",
            bloco,
            flags=re.IGNORECASE
        )
        if not m_val:
            # Fallback: primeiro valor monetário
            m_val = re.search(r"([0-9.]+,\d{2})", bloco)
        
        if m_val:
            valor = _parse_ptbr_number(m_val.group(1))
        
        # Adicionar débito se tiver pelo menos valor
        if valor is not None or cod_receita_denom or periodo:
            debitos.append({
                'item': item_num,
                'codigo_receita_denominacao': cod_receita_denom,
                'periodo_apuracao_debito': periodo,
                'valor': valor,
            })
    
    if debitos:
        p.debitos = debitos
    
    # 8. Total dos Débitos deste Documento
    m_total_debitos = re.search(
        r"Total\s+dos\s+D[eé]bitos\s+(?:deste\s+Documento|do\s+Documento)?\s*[:\-]?\s*([0-9.]+,\d{2})",
        norm,
        flags=re.IGNORECASE
    )
    if m_total_debitos:
        p.total_debitos_documento = _parse_ptbr_number(m_total_debitos.group(1))
    
    # 9. Total do Crédito Original Utilizado neste Documento
    m_total_credito_utilizado = re.search(
        r"Total\s+(?:do\s+)?Cr[eé]dito\s+Original\s+Utilizado\s+(?:neste\s+Documento|no\s+Documento)?\s*[:\-]?\s*([0-9.]+,\d{2})",
        norm,
        flags=re.IGNORECASE
    )
    if m_total_credito_utilizado:
        p.total_credito_original_utilizado = _parse_ptbr_number(m_total_credito_utilizado.group(1))
    
    return p


@dataclass
class PDFReceiptParsed:
    numero_documento: Optional[str] = None
    numero_controle: Optional[str] = None
    autenticacao_serpro: Optional[str] = None
    data_transmissao: Optional[str] = None
    data_hora_recebimento: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            'numero_documento': self.numero_documento,
            'numero_controle': self.numero_controle,
            'autenticacao_serpro': self.autenticacao_serpro,
            'data_transmissao': self.data_transmissao,
            'data_hora_recebimento': self.data_hora_recebimento,
        }


def parse_recibo_pedido_credito_text(txt: str) -> PDFReceiptParsed:
    parsed = PDFReceiptParsed()
    if not txt:
        return parsed

    norm = re.sub(r"[\t\u00A0]+", " ", txt)

    # Buscar "Número da Declaração" ao invés de "Número do Documento"
    m = re.search(r"N[úu]mero\s+da\s+Declara[çc][ãa]o\s*[:\-]?\s*([0-9A-Za-z./\-]+)", norm, flags=re.IGNORECASE)
    if m:
        parsed.numero_documento = m.group(1).strip()

    m = re.search(r"N[úu]mero\s+de\s+Controle\s*[:\-]?\s*([0-9A-Za-z./\-]+)", norm, flags=re.IGNORECASE)
    if m:
        parsed.numero_controle = m.group(1).strip()

    m = re.search(r"Data\s+de\s+Transmiss[aã]o\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})", norm, flags=re.IGNORECASE)
    if m:
        parsed.data_transmissao = m.group(1).strip()

    # Captura data/hora do recebimento para arm zen
    m = re.search(r"em\s+(\d{2}/\d{2}/\d{4})\s+às\s+(\d{2}:\d{2}:\d{2})\s+(\d+)", norm, flags=re.IGNORECASE)
    if m:
        parsed.data_hora_recebimento = f"{m.group(1)} {m.group(2)}"
        parsed.autenticacao_serpro = m.group(3).strip()
    else:
        m_alt = re.search(r"às\s+(\d{2}:\d{2}:\d{2})\s+(\d+)", norm, flags=re.IGNORECASE)
        if m_alt:
            parsed.autenticacao_serpro = m_alt.group(2).strip()

    return parsed


@dataclass
class PDFCreditoContaParsed:
    perdcomp: Optional[str] = None
    data_credito: Optional[str] = None
    valor_credito: Optional[Decimal] = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            'perdcomp': self.perdcomp,
            'data_credito': self.data_credito,
            'valor_credito': str(self.valor_credito) if self.valor_credito is not None else None,
        }


def parse_credito_em_conta_text(txt: str) -> PDFCreditoContaParsed:
    """
    Extrai dados básicos de uma notificação de crédito em conta:
    - PERDCOMP associado
    - Data do crédito (dd/mm/aaaa)
    - Valor creditado (Decimal)
    """
    parsed = PDFCreditoContaParsed()
    if not txt:
        return parsed

    # Normaliza tabs e espaços não separáveis
    norm = re.sub(r"[\t\u00A0]+", " ", txt)

    # Data do crédito ("Informamos que, em 12/03/2024, ...")
    m_data = re.search(r"Informamos que,\s*em\s*(\d{2}/\d{2}/\d{4})", norm, flags=re.IGNORECASE)
    if m_data:
        parsed.data_credito = m_data.group(1)

    # Valor creditado ("no valor de R$ 1.234,56" ou "o valor de 1.234,56")
    m_valor = re.search(r"valor\s+de\s*(?:R\$\s*)?([0-9.\s]+,\d{2})", norm, flags=re.IGNORECASE)
    if not m_valor:
        # Fallback buscando primeira ocorrência de valor após palavra crédito
        credito_section = re.search(r"cr[eé]dito.*?(?:R\$\s*)?([0-9.\s]+,\d{2})", norm, flags=re.IGNORECASE | re.DOTALL)
        if credito_section:
            m_valor = credito_section
    if m_valor:
        parsed.valor_credito = _parse_ptbr_number(m_valor.group(1))

    # PERDCOMP vinculado
    m_perdcomp = re.search(r"Perdcomp\s*(?:n[ºo]\s*)?[:\-]?\s*([0-9A-Za-z./\-]+)", norm, flags=re.IGNORECASE)
    if m_perdcomp:
        candidate = m_perdcomp.group(1).strip().strip(" .;,:")
        if _looks_like_perdcomp(candidate):
            parsed.perdcomp = candidate
    if not parsed.perdcomp:
        candidate = _find_perdcomp_candidate(norm)
        if candidate:
            parsed.perdcomp = candidate

    return parsed


def parse_pedido_credito_text(txt: str) -> PDFParsed:
    """
    Parser específico para PEDIDO DE CRÉDITO (PER).
    
    Tipos suportados:
    - Pedido de Restituição
    - Pedido de Ressarcimento (Compensação)
    
    Extrai:
    - cnpj: CNPJ do contribuinte
    - perdcomp: Número do pedido (PER/DCOMP)
    - metodo_credito: Tipo do documento
    - data_criacao: Data de criação do pedido
    - valor_pedido: Valor solicitado
    - ano: Ano de referência (para ressarcimento)
    - trimestre: Trimestre (para ressarcimento)
    - tipo_credito: Tipo de crédito (para ressarcimento)
    - periodo_apuracao_credito: Período de apuração (para restituição)
    - codigo_receita: Código da receita (para restituição)
    - data_arrecadacao: Data de arrecadação (para restituição)
    """
    p = PDFParsed()
    if not txt:
        return p
    
    # Normalizar
    norm = re.sub(r"[\t\u00A0]+", " ", txt)
    
    # 1. CNPJ (obrigatório)
    m_cnpj = re.search(r"CNPJ\s*[:\-]?\s*([0-9./-]{14,20})", norm, flags=re.IGNORECASE)
    if m_cnpj:
        p.cnpj = _clean_cnpj(m_cnpj.group(1))
    
    # 2. Número do PERDCOMP (PER/DCOMP)
    # Buscar no cabeçalho ou após CNPJ
    if m_cnpj:
        tail = norm[m_cnpj.end():m_cnpj.end() + 100]
        m_per = re.search(r"(\d{5}[\d.\-]+\d{4})", tail)
        if m_per:
            candidate = m_per.group(1).strip()
            if _looks_like_perdcomp(candidate):
                p.perdcomp = candidate
    
    if not p.perdcomp:
        m_per = re.search(r"(?:PERDCOMP|PER\s*/?\s*DCOMP)\s*(?:n[ºo]\s*)?[:\-]?\s*(\d+[\d.\-]+)", norm, flags=re.IGNORECASE)
        if m_per:
            candidate = m_per.group(1).strip()
            if _looks_like_perdcomp(candidate):
                p.perdcomp = candidate
    
    if not p.perdcomp:
        candidate = _find_perdcomp_candidate(norm)
        if candidate:
            p.perdcomp = candidate

    # Determina se é um documento retificador
    if p.perdcomp_inicial and p.perdcomp and p.perdcomp != p.perdcomp_inicial:
        p.is_retificador = True
        p.perdcomp_retificador = p.perdcomp
    elif re.search(r"\bretificador(?:a)?\b", norm, flags=re.IGNORECASE):
        p.is_retificador = True
        if p.perdcomp and not p.perdcomp_retificador:
            p.perdcomp_retificador = p.perdcomp
    
    # 3. Tipo de Documento - determina se é Restituição ou Ressarcimento
    m_tipo = re.search(r"Tipo\s+de\s+Documento\s*[:\-]?\s*(.+?)(?:\n|$)", norm, flags=re.IGNORECASE)
    if m_tipo:
        raw = m_tipo.group(1).strip()
        low = raw.lower()
        
        if 'ressarc' in low:
            p.metodo_credito = 'Pedido de ressarcimento'
        elif 'restitui' in low:
            p.metodo_credito = 'Pedido de restituição'
        else:
            p.metodo_credito = raw
    else:
        # Tentar detectar pelo conteúdo
        whole_lower = norm.lower()
        if 'pedido de ressarcimento' in whole_lower:
            p.metodo_credito = 'Pedido de ressarcimento'
        elif 'pedido de restituição' in whole_lower or 'pedido de restituicao' in whole_lower:
            p.metodo_credito = 'Pedido de restituição'
    
    # 4. Data de Criação
    m_data = re.search(r"Data\s+de\s+Cria[cç][aã]o\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})", norm, flags=re.IGNORECASE)
    if m_data:
        p.data_criacao = m_data.group(1)
    
    # 5. Valor do Pedido
    m_valor = re.search(r"Valor\s+do\s+Pedido.*?([0-9.]+,\d{2})", norm, flags=re.IGNORECASE | re.DOTALL)
    if m_valor:
        p.valor_pedido = _parse_ptbr_number(m_valor.group(1))
    
    # 6. Campos específicos de RESSARCIMENTO
    # Ano
    m_ano = re.search(r"\bAno\b\s*[:\-]?\s*(\d{4})", norm, flags=re.IGNORECASE)
    if m_ano:
        p.ano = m_ano.group(1)
    
    # Trimestre
    m_trim = re.search(r"(\d+)\s*º?\s*Trimestre", norm, flags=re.IGNORECASE)
    if m_trim:
        p.trimestre = m_trim.group(1)
    
    # Tipo de Crédito
    m_tipo_cred = re.search(r"Tipo\s+de\s+Cr[eé]dito\s*[:\-]?\s*(.+?)(?:\n|$)", norm, flags=re.IGNORECASE)
    if m_tipo_cred:
        p.tipo_credito = m_tipo_cred.group(1).strip()
    
    # 7. Campos específicos de RESTITUIÇÃO
    # Período de Apuração (pode ser dd/mm/aaaa ou mm/aaaa)
    m_per_ap = re.search(r"Per[ií]odo\s+de\s+Apura[cç][aã]o\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})", norm, flags=re.IGNORECASE)
    if m_per_ap:
        p.periodo_apuracao_credito = m_per_ap.group(1)
    else:
        m_per_ap = re.search(r"Per[ií]odo\s+de\s+Apura[cç][aã]o\s*[:\-]?\s*(\d{2}/\d{4})", norm, flags=re.IGNORECASE)
        if m_per_ap:
            p.periodo_apuracao_credito = m_per_ap.group(1)
    
    # Código da Receita
    m_rec = re.search(r"C[oó]digo\s+(?:da|de)\s+Receita\s*[:\-]?\s*([0-9.]+)", norm, flags=re.IGNORECASE)
    if m_rec:
        p.codigo_receita = m_rec.group(1).strip()
    
    # Data de Arrecadação
    m_arrec = re.search(r"Data\s+de\s+Arrecada[cç][aã]o\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})", norm, flags=re.IGNORECASE)
    if m_arrec:
        p.data_arrecadacao = m_arrec.group(1)
    
    return p
