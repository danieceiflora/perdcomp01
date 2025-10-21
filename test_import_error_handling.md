# Teste de Tratamento de Erros na Importação de PDFs

## Problema Identificado
Quando um arquivo PDF não contém dados PERDCOMP válidos ou ocorre erro no processamento, o sistema estava reportando como "sucesso" na contagem de arquivos importados, mas o log mostrava erro.

## Correção Implementada

### Mudanças no JavaScript (`adesao_import_lote.html`)

**Antes:**
```javascript
async function processarArquivo(file, criar) {
  const formData = new FormData();
  formData.append('pdf', file);
  formData.append('criar', criar ? '1' : '0');
  
  const resp = await fetch("{% url 'adesao:importar_pdf' %}", {
    method: 'POST',
    headers: { 'X-CSRFToken': getCookie('csrftoken') || '' },
    body: formData
  });
  
  const data = await resp.json();
  
  return {
    ok: data.ok,  // ❌ Problema: assumia que data.ok sempre existe
    file: file.name,
    created: data.created,
    detail_url: data.detail_url,
    fields: data.fields,
    error: data.error
  };
}
```

**Depois:**
```javascript
async function processarArquivo(file, criar) {
  const formData = new FormData();
  formData.append('pdf', file);
  formData.append('criar', criar ? '1' : '0');
  
  try {
    const resp = await fetch("{% url 'adesao:importar_pdf' %}", {
      method: 'POST',
      headers: { 'X-CSRFToken': getCookie('csrftoken') || '' },
      body: formData
    });
    
    const data = await resp.json();
    
    // ✅ Verifica explicitamente se houve erro
    if (!data.ok) {
      return {
        ok: false,
        file: file.name,
        created: false,
        detail_url: null,
        fields: null,
        error: data.error || 'Erro ao processar o arquivo'
      };
    }
    
    // ✅ Retorna sucesso somente se data.ok === true
    return {
      ok: true,
      file: file.name,
      created: data.created || false,
      detail_url: data.detail_url || null,
      fields: data.fields || null,
      error: null
    };
  } catch (error) {
    // ✅ Captura erros de rede ou JSON parsing
    return {
      ok: false,
      file: file.name,
      created: false,
      detail_url: null,
      fields: null,
      error: error.message || 'Erro de rede ao processar o arquivo'
    };
  }
}
```

## Cenários de Erro Tratados

### 1. PDF sem dados PERDCOMP
- **Backend retorna:** `{ok: false, error: "CNPJ não identificado no PDF."}`
- **Resultado:** Card vermelho com mensagem de erro

### 2. Cliente não encontrado
- **Backend retorna:** `{ok: false, error: "Cliente com CNPJ 12345678000100 não encontrado."}`
- **Resultado:** Card vermelho com CNPJ específico

### 3. PERDCOMP duplicado
- **Backend retorna:** `{ok: false, error: "PERDCOMP 123456789 já cadastrado."}`
- **Resultado:** Card vermelho com número do PERDCOMP

### 4. Erro de rede
- **Cenário:** Servidor fora do ar, timeout, etc.
- **Resultado:** Card vermelho com "Erro de rede ao processar o arquivo"

### 5. Erro ao criar adesão (banco de dados)
- **Backend retorna:** `{ok: false, error: "Falha ao criar adesão e débitos: [detalhes]"}`
- **Resultado:** Card vermelho com detalhes do erro

## Como Testar

### Teste 1: PDF sem PERDCOMP
1. Acesse: `http://localhost:8000/adesao/importar-lote/`
2. Selecione um PDF que não seja PERDCOMP (ex: nota fiscal, contrato, etc.)
3. Marque "Criar adesões automaticamente"
4. Clique em "Processar PDFs"

**Resultado Esperado:**
- Card vermelho mostrando: "✗ CNPJ não identificado no PDF."
- Overlay mostra: "1 erro(s) ao processar arquivos"
- Contador: 0 adesões criadas, 1 com erro

### Teste 2: PERDCOMP já cadastrado
1. Importe um PDF válido pela primeira vez (sucesso)
2. Tente importar o mesmo PDF novamente

**Resultado Esperado:**
- Card vermelho mostrando: "✗ PERDCOMP [número] já cadastrado."
- Contador: 0 adesões criadas, 1 com erro

### Teste 3: Mix de sucessos e erros
1. Selecione 5 PDFs:
   - 2 válidos e novos
   - 1 sem PERDCOMP
   - 1 duplicado
   - 1 com cliente inexistente
2. Marque "Criar adesões automaticamente"
3. Clique em "Processar PDFs"

**Resultado Esperado:**
- 2 cards verdes (sucesso)
- 3 cards vermelhos (erros)
- Overlay mostra: "2 adesão(ões) criada(s) com sucesso! (3 com erro)"
- Cada card de erro mostra mensagem específica

### Teste 4: Apenas pré-visualização (sem criar)
1. Selecione PDFs válidos
2. **Desmarque** "Criar adesões automaticamente"
3. Clique em "Processar PDFs"

**Resultado Esperado:**
- Cards mostram dados extraídos (sem criar registros)
- Overlay mostra: "N arquivo(s) processado(s)!"

## Verificação no Console do Navegador

Abra o DevTools (F12) e vá para a aba Console. Durante a importação, você verá:

```javascript
// Para sucesso:
{ok: true, created: true, id: 123, detail_url: "/adesao/123/"}

// Para erro:
{ok: false, error: "CNPJ não identificado no PDF.", ...}
```

## Logs do Servidor

Verifique os logs em `media/import_logs/` para ver detalhes:

```json
{
  "user": "admin",
  "filename": "arquivo_invalido.pdf",
  "ts": "2025-01-21T10:30:00",
  "extracted_present": true,
  "parsed": {
    "cnpj": null,
    "perdcomp": null,
    ...
  }
}
```

## Resumo das Melhorias

✅ **Validação explícita de `data.ok`** antes de considerar sucesso  
✅ **Try-catch** para capturar erros de rede  
✅ **Mensagens de erro específicas** para cada tipo de falha  
✅ **Contadores corretos** de sucesso vs erro  
✅ **Visual consistente** (verde = sucesso, vermelho = erro)  
✅ **Overlay mostra resumo final** com contagem precisa  

## Problemas Resolvidos

❌ **Antes:** 5 arquivos processados, 2 com erro → mostrava "5 adesões criadas"  
✅ **Depois:** 5 arquivos processados, 2 com erro → mostra "3 adesões criadas (2 com erro)"

❌ **Antes:** PDF inválido contava como sucesso  
✅ **Depois:** PDF inválido mostra card vermelho com erro específico
