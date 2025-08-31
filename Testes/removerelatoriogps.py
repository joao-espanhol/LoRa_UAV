def limpar_relatorio(arquivo_entrada, arquivo_saida):
    with open(arquivo_entrada, "r", encoding="utf-8", errors="ignore") as fin, \
         open(arquivo_saida, "w", encoding="utf-8") as fout:
        for linha in fin:
            if linha.strip() != "--- RELATÓRIO GPS ---":
                fout.write(linha)

# exemplo de uso
limpar_relatorio("30AGOTXcopy.txt", "30AGOTXcopylimpo.txt")
