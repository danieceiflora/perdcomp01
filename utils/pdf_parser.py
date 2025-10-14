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


@dataclass
class PDFParsed:
    cnpj: Optional[str] = None
    perdcomp: Optional[str] = None
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
    #   'codigo_receita_denominacao': str | None,
    #   'periodo_apuracao_debito': str | None,
    #   'valor': Decimal | None,
    # }
    debitos: List[Dict[str, Any]] = field(default_factory=list)
    # Valor Total na seção 'Origem do Crédito' (usado como saldo do crédito)
    valor_total_origem: Optional[Decimal] = None
    # Valor Original do Crédito Inicial (bloco 'CRÉDITO PAGAMENTO INDEVIDO OU A MAIOR' ou similar)
    valor_original_credito_inicial: Optional[Decimal] = None

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

    # CNPJ e PERDCOMP (primeiro token após o CNPJ na mesma linha)
    m = re.search(r"CNPJ\s*[:\-]?\s*([0-9./-]{14,20})\s+([0-9A-Za-z._\-]{8,})", norm, flags=re.IGNORECASE)
    if m:
        p.cnpj = _clean_cnpj(m.group(1))
        p.perdcomp = m.group(2).strip()
    else:
        # CNPJ isolado (sem PERDCOMP na mesma linha)
        m_cnpj = re.search(r"CNPJ\s*[:\-]?\s*([0-9./-]{14,20})", norm, flags=re.IGNORECASE)
        if m_cnpj:
            p.cnpj = _clean_cnpj(m_cnpj.group(1))
        # Fallback arriscado: pode capturar a versão '8.3' do cabeçalho, portanto usamos apenas se tiver formato típico
        m_per = re.search(r"PERDCOMP\s*[:\-]?\s*([0-9]{2,}\.[0-9A-Za-z.\-]+)", norm, flags=re.IGNORECASE)
        if m_per:
            p.perdcomp = m_per.group(1).strip()

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
                # Fallback genérico
                p.metodo_credito = 'Compensação vinculada a um pedido de restituição'
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
    for blk in re.finditer(r"(?ms)^\s*\d{1,3}\s*\.\s*D[eé]bito\s*(.*?)(?=^\s*\d{1,3}\s*\.\s*D[eé]bito|\Z)", norm):
        block = blk.group(0)
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

    return p
