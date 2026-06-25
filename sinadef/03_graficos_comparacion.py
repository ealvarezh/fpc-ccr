import sys, os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# ── Load data ──
OUT = r'C:\estela\github\fpc\output'
df = pd.read_csv(os.path.join(OUT, 'comparacion_nacional_grupo110.csv'))
df_total = pd.read_csv(os.path.join(OUT, 'comparacion_total_anual.csv'))
df_g10 = pd.read_csv(os.path.join(OUT, 'comparacion_nacional_grupo10.csv'))

YEARS = sorted(df['year'].unique())
LATEST_YEAR = YEARS[-1]

# ── Style ──
plt.rcParams.update({'font.size': 8, 'axes.titlesize': 11, 'figure.dpi': 150})

# ============================================================================
# FIGURE 1: Total annual comparison (SINADEF vs INEI)
# ============================================================================
fig, ax = plt.subplots(figsize=(9, 4.5))
x = np.arange(len(YEARS))
w = 0.35
ax.bar(x - w/2, df_total['ndefun_sinadef'], w, label='SINADEF (crudo)', color='#E74C3C', alpha=0.85)
ax.bar(x + w/2, df_total['ndefun_inei'], w, label='INEI (procesado)', color='#3498DB', alpha=0.85)
for i, (s, e, pct) in enumerate(zip(df_total['ndefun_sinadef'], df_total['ndefun_inei'], df_total['pct_diferencia'])):
    ax.text(i, max(s, e) + 2000, f'{pct:.0f}%', ha='center', fontsize=7, color='#555555')
ax.set_xticks(x)
ax.set_xticklabels(YEARS)
ax.set_ylabel('N.º defunciones')
ax.set_title('Total anual de defunciones: SINADEF crudo vs INEI procesado')
ax.legend(fontsize=8)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v/1000:.0f}k'))
fig.tight_layout()
plt.show()
# ============================================================================
# FIGURE 2: 10 broad groups — stacked bars for latest year
# ============================================================================
g10_latest = df_g10[df_g10['year'] == LATEST_YEAR].copy()
g10_latest['pct_sinadef'] = g10_latest['ndefun_sinadef'] / g10_latest['ndefun_sinadef'].sum() * 100
g10_latest['pct_inei'] = g10_latest['ndefun_inei'] / g10_latest['ndefun_inei'].sum() * 100
g10_latest = g10_latest.sort_values('pct_inei', ascending=True)

fig, ax = plt.subplots(figsize=(9, 5))
y_pos = np.arange(len(g10_latest))
h = 0.35
ax.barh(y_pos - h/2, g10_latest['pct_sinadef'], h, label='SINADEF', color='#E74C3C', alpha=0.85)
ax.barh(y_pos + h/2, g10_latest['pct_inei'], h, label='INEI', color='#3498DB', alpha=0.85)
ax.set_yticks(y_pos)
ax.set_yticklabels(g10_latest['ggrupos'], fontsize=7.5)
ax.set_xlabel('% del total de defunciones')
ax.set_title(f'Distribución por 10 grandes grupos ({LATEST_YEAR})')
ax.legend(fontsize=8)
fig.tight_layout()
plt.show()
# ============================================================================
# FIGURE 3: Top 30 causas — scatter SINADEF vs INEI (latest year)
# ============================================================================
df_latest = df[df['year'] == LATEST_YEAR].copy()
df_latest = df_latest[df_latest['grupo110'] != 'Resto de las demas enfermedades']
top30 = df_latest.nlargest(30, 'ndefun_inei')

fig, ax = plt.subplots(figsize=(10, 8))
max_val = max(top30['ndefun_sinadef'].max(), top30['ndefun_inei'].max())
ax.plot([0, max_val], [0, max_val], 'k--', alpha=0.3, linewidth=0.8)
sc = ax.scatter(top30['ndefun_inei'], top30['ndefun_sinadef'],
                c=top30['pct_diferencia'].abs(), cmap='Reds', s=60, edgecolors='#333333', linewidth=0.3)
for _, r in top30.iterrows():
    ax.annotate(r['grupo110'][:45], (r['ndefun_inei'], r['ndefun_sinadef']),
                fontsize=5.5, alpha=0.75, ha='left',
                xytext=(4, 2), textcoords='offset points')
cbar = plt.colorbar(sc, ax=ax, shrink=0.75)
cbar.set_label('|% diferencia| vs INEI', fontsize=7)
ax.set_xlabel('INEI (ndefun_)')
ax.set_ylabel('SINADEF (crudo)')
ax.set_title(f'Top 30 causas: SINADEF vs INEI ({LATEST_YEAR})')
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v/1000:.0f}k'))
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v/1000:.0f}k'))
fig.tight_layout()
plt.show()
# ============================================================================
# FIGURE 4: Heatmap — match % by year × selected top causes
# ============================================================================
top_causes = df.groupby('grupo110')['ndefun_inei'].sum().nlargest(20).index.tolist()
heat_df = df[df['grupo110'].isin(top_causes)].pivot_table(
    index='grupo110', columns='year', values='ratio', aggfunc='first')
heat_df = heat_df.reindex(top_causes)

fig, ax = plt.subplots(figsize=(10, 7))
im = ax.imshow(heat_df.values, aspect='auto', cmap='RdYlGn', vmin=0, vmax=1.2)
ax.set_xticks(range(len(heat_df.columns)))
ax.set_xticklabels(heat_df.columns, fontsize=7.5)
ax.set_yticks(range(len(heat_df.index)))
ax.set_yticklabels([s[:50] for s in heat_df.index], fontsize=6.5)
for i in range(len(heat_df.index)):
    for j in range(len(heat_df.columns)):
        v = heat_df.values[i, j]
        color = 'white' if (v < 0.3 or v > 1.5 or np.isnan(v)) else 'black'
        txt = f'{v:.2f}' if not np.isnan(v) else '-'
        ax.text(j, i, txt, ha='center', va='center', fontsize=5.5, color=color)
cbar = plt.colorbar(im, ax=ax, shrink=0.8)
cbar.set_label('ratio SINADEF/INEI', fontsize=7)
ax.set_title('Ratio SINADEF / INEI por año — Top 20 causas', fontsize=9)
fig.tight_layout()
plt.show()
# ============================================================================
# FIGURE 5: Variation trend by year — boxplot of pct_diferencia across causes
# ============================================================================
df_no_resto = df[df['grupo110'] != 'Resto de las demas enfermedades'].copy()
df_no_resto['pct_diferencia_clipped'] = df_no_resto['pct_diferencia'].clip(-200, 200)
years_data = [df_no_resto[df_no_resto['year']==y]['pct_diferencia_clipped'].dropna().values for y in YEARS]

fig, ax = plt.subplots(figsize=(9, 5))
bp = ax.boxplot(years_data, labels=YEARS, patch_artist=True, showmeans=True,
                meanprops=dict(marker='D', markerfacecolor='black', markersize=4))
for patch, color in zip(bp['boxes'], plt.cm.RdYlGn(np.linspace(0.15, 0.85, len(YEARS)))):
    patch.set_facecolor(color)
ax.axhline(y=0, color='black', linewidth=0.5, linestyle='--')
ax.set_ylabel('% diferencia vs INEI')
ax.set_title('Distribución de la variación por causa a través de los años\n(sin "Resto de las demás enfermedades")')
fig.tight_layout()
plt.show()
# ============================================================================
# FIGURE 6: Treemap-style — distribución porcentual comparada (latest year)
# ============================================================================
df_latest_pct = df_latest.copy()
total_sin = df_latest_pct['ndefun_sinadef'].sum()
total_inei = df_latest_pct['ndefun_inei'].sum()
df_latest_pct['pct_sinadef'] = df_latest_pct['ndefun_sinadef'] / total_sin * 100
df_latest_pct['pct_inei'] = df_latest_pct['ndefun_inei'] / total_inei * 100
df_latest_pct['pct_diff_abs'] = (df_latest_pct['pct_inei'] - df_latest_pct['pct_sinadef']).abs()
top_diff = df_latest_pct.nlargest(15, 'pct_diff_abs')

fig, ax = plt.subplots(figsize=(9, 5.5))
y_pos = np.arange(len(top_diff))
h = 0.35
ax.barh(y_pos - h/2, top_diff['pct_sinadef'], h, label='% SINADEF', color='#E74C3C', alpha=0.85)
ax.barh(y_pos + h/2, top_diff['pct_inei'], h, label='% INEI', color='#3498DB', alpha=0.85)
ax.set_yticks(y_pos)
ax.set_yticklabels([s[:55] for s in top_diff['grupo110']], fontsize=7)
ax.set_xlabel('% del total')
ax.set_title(f'Top 15 causas con mayor diferencia en distribución porcentual ({LATEST_YEAR})')
ax.legend(fontsize=8)
fig.tight_layout()
plt.show()
