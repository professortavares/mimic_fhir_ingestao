---
name: evoluir-ingestao-fhir
description: Evolui o projeto MIMIC FHIR para ingerir um novo arquivo NDJSON/NDJSON.GZ em PostgreSQL, mantendo arquitetura, Docker, logs, testes e README existentes.
---

# Evoluir ingestão FHIR

Use esta skill para adicionar a ingestão de um novo recurso FHIR ao projeto existente.

Entrada esperada:

```text
$ARGUMENTS
````

A chamada deve informar, em texto livre:

* arquivo;
* recurso FHIR;
* campos a importar;
* FK/relacionamento, se houver.

Exemplo:

```bash
/evoluir-ingestao-fhir arquivo=./data/MimicLocation.ndjson.gz recurso=Location campos=id,name fk=Organization
```

## Instruções

1. Analise a arquitetura atual de ingestão antes de alterar código.
2. Reaproveite o padrão existente de:

   * Docker;
   * logs;
   * testes;
   * migrations/tabelas;
   * código em português;
   * README.
3. Analise o arquivo informado em `$ARGUMENTS`.
4. Importe somente os campos solicitados.
5. Crie ou atualize a tabela necessária.
6. Crie FK quando o relacionamento for informado.
7. Garanta a ordem correta de ingestão entre tabelas dependentes.
8. Não versione arquivos `.gz`.
9. Atualize testes e README.
10. Evite refatorações fora do escopo.

## Regras FHIR

Quando houver FK, procure referências no padrão FHIR, como:

* `Organization/abc`;
* `Location/abc`;
* `Patient/abc`.

Extraia apenas o ID referenciado.

Para Location com Organization, procure especialmente:

```text
managingOrganization.reference
```

## Resultado esperado

Ao final, informe:

* arquivos alterados;
* tabela criada/alterada;
* campos importados;
* FK criada, se houver;
* comando Docker para executar;
* testes executados;
* limitações encontradas.