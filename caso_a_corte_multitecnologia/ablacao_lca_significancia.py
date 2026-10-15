"""
ablacao_lca_significancia.py
==============================
Fecha o item de ablação do Caso A (Seção 1.6/6 do plano: "Ablação:
LCA on/off no conjunto Profiles/CPPLib" -- marcado "Planejada", nunca
formalmente fechado com teste de significância). Os dados BRUTOS da
ablação já existiam (`resultado_heuristica_cpplib.csv`, gerado por
`rodar_heuristica_cpplib.py`, que já roda os 2 modos -- "original"
= `enforce_precedence=False`, "com_pi" = `enforce_precedence=True`,
mecanismo LCA -- nas 84 instâncias reais válidas do CPPLib/Profiles)
-- faltava só a camada de significância estatística formal.

Reaproveita a metodologia de `pcgtsp_comparison/significancia_estatistica.py`
(LCPP-main, Seção 1.6 do plano pede explicitamente pra reaproveitar esse
arquivo): Wilcoxon signed-rank (H0: mediana do delta = 0) + effect size
(correlação rank-biserial pareada) + IC 95% bootstrap da média -- MESMAS
funções (`rank_biserial`, `bootstrap_ci_mean`, `relatar`), copiadas aqui
porque o arquivo original vive num projeto irmão (`LCPP-main`) fora
desta pasta, não por reimplementação divergente.

Desenho da ablação: comparação PAREADA por instância (mesma instância,
mesma heurística, só a config `enforce_precedence` muda -- sem
aleatoriedade envolvida nesta heurística construtiva, então n=84 pares
de instância é a unidade de comparação correta aqui, diferente da
comparação de 3 métodos do Caso A [Seção 1.6], que precisou de 10
sementes porque TSH+VNS/MASTRI/PCGLNS têm componente estocástico --
esta heurística geométrica não tem).

RESULTADO (31/08/2026, validado com o Gemini como segunda opinião
crítica sobre a própria estatística -- não só sobre o resultado):

- **Violações de precedência (Π) -- o efeito que o mecanismo existe pra
  produzir:** `original` (LCA off) viola 96,5% de todos os pares Π
  verificados nas 84 instâncias (4.433/4.596, média 52,77/instância);
  `com_pi` (LCA on) reduz pra 0,5% (21/4.596, média 0,25/instância) --
  **redução agregada de 99,53%**. 79/84 instâncias (94%) chegam a Π=0
  perfeito. **Limitação real, não escondida:** 5/84 instâncias (6%)
  mantêm violações residuais pequenas (1-6 pares) mesmo com o mecanismo
  ligado -- rastreado até o "recuo LOCAL parcial" já documentado no
  próprio código (`heuristic_core.py`, tratamento de subárvore em
  conflito, linhas ~1180/1264) pra certas topologias de conflito, não
  um bug novo. **O mecanismo reduz drasticamente mas não GARANTE Π=0 em
  100% dos casos** -- a reivindicação correta é "quase sempre" (94%),
  não "sempre".
- **Custo em FO:** gap médio com_pi vs. original = **+1,27%** (mediana
  +1,27%, desvio 0,33%, IC 95% bootstrap [+1,20%, +1,34%]) -- custo
  pequeno e estreito pela quase-eliminação das violações. 84/84
  instâncias com gap positivo (ligar o mecanismo nunca é mais barato,
  como esperado teoricamente).
- **Ressalva estatística importante (apontada pelo Gemini, incorporada
  aqui em vez de ignorada):** o teste de Wilcoxon (p=1,7×10⁻¹⁵) foi
  calculado, mas é estatisticamente SUPÉRFLUO aqui -- a heurística é
  DETERMINÍSTICA (sem sementes/aleatoriedade), então as 84 instâncias
  não são uma AMOSTRA de uma população maior a ser inferida, são a
  população inteira relevante já observada por completo. O fato de
  84/84 diferenças terem o mesmo sinal (rank-biserial r=+1,00) já É a
  evidência conclusiva, sem precisar de teste de hipótese pra "provar"
  significância -- mantido no relatório por consistência de formato com
  as outras comparações do projeto (que usam sementes de verdade), não
  porque adiciona rigor além do que "positivo em 84/84 casos" já mostra
  por si só.
- **Tempo:** overhead desprezível (1,37s → 1,44s, ~5%).

**Conclusão honesta pro Caso A:** o mecanismo LCA de imposição de
precedência é altamente eficaz (quase elimina violações, ~94% dos casos
perfeitos) a um custo pequeno e estatisticamente estreito em FO -- mas
"quase sempre garante Π", não "sempre garante Π" -- ressalva que deve
entrar explicitamente em qualquer alegação de "garantia" na redação
final do Caso A.
"""
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon


def rank_biserial(diffs):
    diffs = np.asarray(diffs, dtype=float)
    diffs = diffs[diffs != 0]
    n = len(diffs)
    ranks = pd.Series(np.abs(diffs)).rank().values
    w_pos = ranks[diffs > 0].sum()
    w_neg = ranks[diffs < 0].sum()
    total = n * (n + 1) / 2
    assert abs((w_pos + w_neg) - total) < 1e-6
    r = (w_pos - w_neg) / total
    return r, w_pos, w_neg


def bootstrap_ci_mean(x, n_boot=20000, alpha=0.05, seed=0):
    x = np.asarray(x, dtype=float)
    r = np.random.default_rng(seed)
    boots = np.array([r.choice(x, size=len(x), replace=True).mean() for _ in range(n_boot)])
    lo, hi = np.percentile(boots, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return lo, hi


def relatar(nome, deltas):
    deltas = np.asarray(deltas, dtype=float)
    n = len(deltas)
    n_neg, n_pos, n_zero = (deltas < 0).sum(), (deltas > 0).sum(), (deltas == 0).sum()
    stat, p = wilcoxon(deltas, zero_method="wilcox", alternative="two-sided", method="auto")
    r, w_pos, w_neg = rank_biserial(deltas)
    lo, hi = bootstrap_ci_mean(deltas)
    print(f"\n=== {nome} (n={n}) ===")
    print(f"  media={deltas.mean():+.4f}%  mediana={np.median(deltas):+.4f}%  desvio={deltas.std(ddof=1):.4f}%")
    print(f"  sinais: neg={n_neg} pos={n_pos} zero={n_zero}")
    print(f"  Wilcoxon signed-rank (H0: mediana=0): statistic={stat:.2f}  p={p:.3e}")
    print(f"  effect size (correlacao rank-biserial pareada) r={r:+.4f}")
    print(f"  IC 95% bootstrap da media: [{lo:+.4f}%, {hi:+.4f}%]")
    return {"nome": nome, "n": n, "media_pct": deltas.mean(), "mediana_pct": np.median(deltas),
            "wilcoxon_p": p, "rank_biserial_r": r, "ic95_lo": lo, "ic95_hi": hi}


if __name__ == "__main__":
    df = pd.read_csv("resultado_heuristica_cpplib.csv")
    df_ok = df[df["skipped"].isna() | (df["skipped"] == "")]
    print(f"{len(df_ok)}/{len(df)} instancias validas ({(df['skipped'].notna() & (df['skipped']!='')).sum()} "
          f"excluida(s): {df[df['skipped'].notna() & (df['skipped']!='')]['instance'].tolist()})")

    # --- 1. Custo (FO): com_pi (LCA on) vs. original (LCA off) ---
    resultado_fo = relatar("Gap % de FO -- com_pi (LCA on) vs. original (LCA off), n=84 instancias CPPLib",
                            df_ok["gap_pct_pi_vs_original"])

    # --- 2. Violacoes de precedencia (Pi) -- o efeito que a ablacao existe pra medir ---
    total_orig = df_ok["original_prec_violations"].sum()
    total_com_pi = df_ok["com_pi_prec_violations"].sum()
    total_pares = df_ok["n_precedence_pairs"].sum()
    reducao_pct = 100 * (1 - total_com_pi / total_orig)
    n_perfeitas = (df_ok["com_pi_prec_violations"] == 0).sum()
    residuais = df_ok[df_ok["com_pi_prec_violations"] > 0]

    print(f"\n=== Violacoes de precedencia (Pi) -- efeito principal do mecanismo LCA ===")
    print(f"  total de pares Pi verificados: {total_pares:.0f}")
    print(f"  original (enforce_precedence=False): {total_orig:.0f} violacoes  "
          f"(media/instancia={df_ok['original_prec_violations'].mean():.2f}, "
          f"{100*total_orig/total_pares:.1f}% dos pares)")
    print(f"  com_pi (enforce_precedence=True, LCA): {total_com_pi:.0f} violacoes  "
          f"(media/instancia={df_ok['com_pi_prec_violations'].mean():.2f}, "
          f"{100*total_com_pi/total_pares:.1f}% dos pares)")
    print(f"  reducao agregada: {reducao_pct:.2f}%")
    print(f"  instancias com Pi=0 perfeito: {n_perfeitas}/{len(df_ok)} ({100*n_perfeitas/len(df_ok):.1f}%)")
    print(f"  instancias com violacao residual (recuo LOCAL parcial, ver heuristic_core.py "
          f"linhas ~1180/1264): {len(residuais)}/{len(df_ok)}")
    if len(residuais) > 0:
        print(residuais[["instance", "com_pi_prec_violations", "n_precedence_pairs",
                          "original_prec_violations"]].to_string(index=False))

    # --- 3. Tempo e feasibility geometrica (Pi != feasibility -- ok/timeout sao outra checagem) ---
    print(f"\n=== Feasibility geometrica e tempo ===")
    print(f"  original_ok=True: {(df_ok['original_ok']==True).sum()}/{len(df_ok)}  "
          f"com_pi_ok=True: {(df_ok['com_pi_ok']==True).sum()}/{len(df_ok)}  "
          f"timeouts: {(df_ok['com_pi_timeout']==True).sum()}/{len(df_ok)}")
    print(f"  tempo medio original={df_ok['original_time_s'].mean():.3f}s  "
          f"tempo medio com_pi={df_ok['com_pi_time_s'].mean():.3f}s")

    out = pd.DataFrame([resultado_fo])
    out.to_csv("ablacao_lca_significancia.csv", index=False)
    print("\nSalvo em ablacao_lca_significancia.csv")
