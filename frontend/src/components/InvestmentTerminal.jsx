import { useState, useEffect, useRef } from "react";
import { API_BASE_URL } from "../config";


// Transformation layer: maps backend ReportOutput to frontend UI structure
function transformBackendReport(backendReport) {
  if (!backendReport) return null;

  const currentPrice = backendReport.fundamentals?.current_price || 0;

  // Calculate upside percentages for quant scenarios
  const calculateUpside = (target) => {
    if (!target || !currentPrice) return 0;
    return ((target - currentPrice) / currentPrice) * 100;
  };

  // Derive risk level from risk analysis severity
  const deriveRiskLevel = (risks) => {
    if (!risks || risks.length === 0) return "Moderate";
    const hasCritical = risks.some(r => r.severity === "Critical");
    const hasHigh = risks.some(r => r.severity === "High");
    if (hasCritical) return "Very High";
    if (hasHigh) return "High";
    const mediumCount = risks.filter(r => r.severity === "Medium").length;
    if (mediumCount >= 3) return "Moderate";
    return "Low";
  };

  return {
    ticker: backendReport.ticker,
    company_name: backendReport.company_name,
    executive_summary: {
      recommendation: backendReport.executive_summary?.recommendation || "Hold",
      conviction_score: backendReport.executive_summary?.conviction_score || 50,
      key_catalyst: backendReport.executive_summary?.key_catalyst || "",
      entry_zone: backendReport.executive_summary?.entry_zone || "",
      price_targets: backendReport.executive_summary?.price_targets || {},
    },
    fundamentals: {
      current_price: backendReport.fundamentals?.current_price,
      market_cap: backendReport.fundamentals?.market_cap,
      pe_ratio: backendReport.fundamentals?.pe_ratio,
      forward_pe: backendReport.fundamentals?.forward_pe,
      eps: backendReport.fundamentals?.eps,
      revenue_growth: backendReport.fundamentals?.revenue_growth,
      free_cash_flow: backendReport.fundamentals?.free_cash_flow,
      debt_to_equity: backendReport.fundamentals?.debt_to_equity,
      profit_margins: backendReport.fundamentals?.profit_margins,
      interpretation: backendReport.fundamentals?.interpretation || "",
    },
    technical_indicators: {
      rsi: backendReport.technicals?.rsi,
      macd: null, // Backend doesn't provide MACD
      macd_signal: null,
      macd_histogram: null,
      macd_bullish: null,
      sma_50: backendReport.technicals?.sma_50,
      sma_200: backendReport.technicals?.sma_200,
      golden_cross: backendReport.technicals?.golden_cross || false,
      death_cross: backendReport.technicals?.death_cross || false,
      overbought: backendReport.technicals?.overbought || false,
      oversold: backendReport.technicals?.oversold || false,
      volume_ratio: null, // Backend doesn't provide volume ratio
      trend: backendReport.technicals?.volume_trend === "increasing" ? "Bullish" : 
             backendReport.technicals?.volume_trend === "decreasing" ? "Bearish" : "Neutral",
    },
    risk_metrics: {
      volatility: backendReport.risk_metrics?.volatility ?? null,
      max_drawdown: backendReport.risk_metrics?.max_drawdown ?? null,
      sharpe_ratio: backendReport.risk_metrics?.sharpe_ratio ?? null,
      beta: backendReport.risk_metrics?.beta ?? null,
      risk_level: backendReport.risk_metrics?.risk_level ?? deriveRiskLevel(backendReport.risk_analysis?.risks),
    },
    quant_scenarios: {
      current_price: currentPrice,
      bull: {
        target: backendReport.scenario_analysis?.bull_case?.target_price,
        probability: backendReport.scenario_analysis?.bull_probability || 33,
        upside_pct: calculateUpside(backendReport.scenario_analysis?.bull_case?.target_price),
      },
      base: {
        target: backendReport.scenario_analysis?.base_case?.target_price,
        probability: backendReport.scenario_analysis?.base_probability || 34,
        upside_pct: calculateUpside(backendReport.scenario_analysis?.base_case?.target_price),
      },
      bear: {
        target: backendReport.scenario_analysis?.bear_case?.target_price,
        probability: backendReport.scenario_analysis?.bear_probability || 33,
        upside_pct: calculateUpside(backendReport.scenario_analysis?.bear_case?.target_price),
      },
    },
    news_sentiment: {
      overall_score: backendReport.news_sentiment?.overall_score || 0,
      overall_label: backendReport.news_sentiment?.overall_label || "neutral",
      articles: backendReport.news_sentiment?.articles || [],
      top_positive_drivers: backendReport.news_sentiment?.top_positive_drivers || [],
      top_negative_drivers: backendReport.news_sentiment?.top_negative_drivers || [],
    },
    analyst_consensus: {
      strong_buy: backendReport.analyst_consensus?.strong_buy || 0,
      buy: backendReport.analyst_consensus?.buy || 0,
      hold: backendReport.analyst_consensus?.hold || 0,
      sell: backendReport.analyst_consensus?.sell || 0,
      strong_sell: backendReport.analyst_consensus?.strong_sell || 0,
      mean_target_price: backendReport.analyst_consensus?.mean_target_price,
      summary: backendReport.analyst_consensus?.summary || "",
    },
    scenario_analysis: {
      bull_case: {
        target_price: backendReport.scenario_analysis?.bull_case?.target_price,
        narrative: backendReport.scenario_analysis?.bull_case?.narrative || "",
      },
      base_case: {
        target_price: backendReport.scenario_analysis?.base_case?.target_price,
        narrative: backendReport.scenario_analysis?.base_case?.narrative || "",
      },
      bear_case: {
        target_price: backendReport.scenario_analysis?.bear_case?.target_price,
        narrative: backendReport.scenario_analysis?.bear_case?.narrative || "",
      },
      bull_probability: backendReport.scenario_analysis?.bull_probability || 33,
      base_probability: backendReport.scenario_analysis?.base_probability || 34,
      bear_probability: backendReport.scenario_analysis?.bear_probability || 33,
    },
    risk_analysis: {
      risks: backendReport.risk_analysis?.risks || [],
    },
    timing_analysis: {
      should_buy_now: backendReport.timing_analysis?.should_buy_now || false,
      reasoning: backendReport.timing_analysis?.reasoning || "",
    },
    ai_report: {
      investment_thesis: backendReport.ai_report?.investment_thesis || "",
      growth_drivers: backendReport.ai_report?.growth_drivers || "",
      risks: backendReport.ai_report?.risks || "",
      valuation_view: backendReport.ai_report?.valuation_view || "",
      recommendation: backendReport.ai_report?.recommendation || "",
      conclusion: backendReport.ai_report?.conclusion || "",
    },
  };
}

const css = `
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&family=Bebas+Neue&display=swap');

  :root {
    --bg: #050505;
    --surface: #111111;
    --surface2: #1A1A1A;
    --surface3: #222222;
    --accent: #DFFF2F;
    --accent-dim: rgba(223,255,47,0.12);
    --accent-glow: rgba(223,255,47,0.25);
    --text: #FFFFFF;
    --text-muted: #BDBDBD;
    --text-dim: #666666;
    --success: #65FF8A;
    --success-dim: rgba(101,255,138,0.12);
    --warning: #FFD84D;
    --warning-dim: rgba(255,216,77,0.12);
    --danger: #FF5A5A;
    --danger-dim: rgba(255,90,90,0.12);
    --border: rgba(255,255,255,0.08);
    --border-accent: rgba(223,255,47,0.3);
    --font-display: 'Bebas Neue', sans-serif;
    --font-body: 'Space Grotesk', sans-serif;
    --font-mono: 'Space Mono', monospace;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  .terminal-root {
    background: var(--bg);
    color: var(--text);
    font-family: var(--font-body);
    min-height: 100vh;
    position: relative;
    overflow-x: hidden;
  }

  .grid-bg {
    position: fixed;
    inset: 0;
    background-image:
      linear-gradient(rgba(223,255,47,0.02) 1px, transparent 1px),
      linear-gradient(90deg, rgba(223,255,47,0.02) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none;
    z-index: 0;
  }

  .radial-bg {
    position: fixed;
    top: -30%;
    right: -20%;
    width: 70vw;
    height: 70vw;
    background: radial-gradient(ellipse, rgba(223,255,47,0.04) 0%, transparent 65%);
    pointer-events: none;
    z-index: 0;
  }

  .content-wrap {
    position: relative;
    z-index: 1;
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 24px 200px;
  }

  /* TOP NAV */
  .top-nav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 20px 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 0;
  }

  .nav-brand {
    font-family: var(--font-mono);
    font-size: 11px;
    letter-spacing: 0.2em;
    color: var(--accent);
    text-transform: uppercase;
  }

  .nav-status {
    display: flex;
    align-items: center;
    gap: 20px;
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--text-dim);
    letter-spacing: 0.1em;
  }

  .status-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--success);
    box-shadow: 0 0 8px var(--success);
    animation: pulse-dot 2s ease-in-out infinite;
    display: inline-block;
    margin-right: 6px;
  }

  @keyframes pulse-dot {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
  }

  /* SECTION LABEL */
  .section-label {
    font-family: var(--font-mono);
    font-size: 10px;
    letter-spacing: 0.25em;
    color: var(--accent);
    text-transform: uppercase;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .section-label::after {
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, var(--border-accent), transparent);
  }

  /* HERO SECTION */
  .hero {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 48px;
    align-items: center;
    padding: 60px 0 48px;
    border-bottom: 1px solid var(--border);
    position: relative;
  }

  .hero-left {}

  .hero-ticker {
    font-family: var(--font-display);
    font-size: clamp(100px, 14vw, 180px);
    line-height: 0.85;
    color: var(--text);
    letter-spacing: -2px;
    position: relative;
    display: inline-block;
  }

  .hero-ticker::before {
    content: attr(data-ticker);
    position: absolute;
    inset: 0;
    color: var(--accent);
    clip-path: polygon(0 0, 100% 0, 100% 40%, 0 40%);
  }

  .hero-company {
    font-size: 14px;
    color: var(--text-muted);
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-top: 12px;
    font-family: var(--font-mono);
  }

  .hero-meta {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-top: 24px;
    flex-wrap: wrap;
  }

  .hero-price {
    font-family: var(--font-display);
    font-size: 48px;
    color: var(--text);
    line-height: 1;
  }

  .hero-price-label {
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--text-dim);
    letter-spacing: 0.15em;
    margin-bottom: 4px;
  }

  /* CONVICTION BLOCK */
  .conviction-block {
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0;
  }

  .conviction-iso {
    width: 200px;
    height: 200px;
    position: relative;
  }

  .conviction-number {
    font-family: var(--font-display);
    font-size: 96px;
    line-height: 1;
    color: var(--accent);
    text-align: center;
    text-shadow: 0 0 40px rgba(223,255,47,0.5);
  }

  .conviction-denom {
    font-family: var(--font-mono);
    font-size: 14px;
    color: var(--text-muted);
    text-align: center;
    letter-spacing: 0.1em;
    margin-top: -8px;
  }

  .conviction-label {
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--text-dim);
    text-align: center;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin-bottom: 8px;
  }

  .rec-badge {
    padding: 12px 32px;
    font-family: var(--font-display);
    font-size: 32px;
    letter-spacing: 3px;
    border: 2px solid;
    display: inline-block;
    text-align: center;
    margin-top: 8px;
    position: relative;
  }

  .rec-badge.buy {
    color: var(--success);
    border-color: var(--success);
    background: rgba(101,255,138,0.06);
    box-shadow: 0 0 30px rgba(101,255,138,0.15), inset 0 0 30px rgba(101,255,138,0.05);
  }

  .rec-badge.hold {
    color: var(--warning);
    border-color: var(--warning);
    background: rgba(255,216,77,0.06);
    box-shadow: 0 0 30px rgba(255,216,77,0.15);
  }

  .rec-badge.sell {
    color: var(--danger);
    border-color: var(--danger);
    background: rgba(255,90,90,0.06);
    box-shadow: 0 0 30px rgba(255,90,90,0.15);
  }

  .rec-badge::before {
    content: '';
    position: absolute;
    top: -1px; left: -1px; right: -1px; bottom: -1px;
    border: 1px solid;
    border-color: inherit;
    opacity: 0.3;
    transform: translate(4px, 4px);
  }

  /* EXECUTIVE SECTION */
  .exec-section {
    padding: 60px 0 48px;
    border-bottom: 1px solid var(--border);
  }

  .exec-heading {
    font-family: var(--font-display);
    font-size: clamp(48px, 6vw, 80px);
    line-height: 0.9;
    letter-spacing: 2px;
    margin-bottom: 40px;
    color: var(--text);
  }

  .exec-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 1px;
    background: var(--border);
  }

  .exec-cell {
    background: var(--bg);
    padding: 28px 24px;
    position: relative;
  }

  .exec-cell:first-child {
    grid-column: 1 / -1;
    border-bottom: 1px solid var(--border);
  }

  .exec-cell-label {
    font-family: var(--font-mono);
    font-size: 10px;
    letter-spacing: 0.2em;
    color: var(--accent);
    text-transform: uppercase;
    margin-bottom: 12px;
  }

  .exec-cell-value {
    font-size: 15px;
    color: var(--text);
    line-height: 1.6;
  }

  .exec-cell-value.large {
    font-size: 22px;
    font-weight: 600;
    line-height: 1.3;
  }

  /* FUNDAMENTALS */
  .fundamentals-section {
    padding: 60px 0 48px;
    border-bottom: 1px solid var(--border);
  }

  .fund-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 1px;
    background: var(--border);
    margin-bottom: 32px;
  }

  .fund-block {
    background: var(--surface);
    padding: 24px 20px;
    position: relative;
    overflow: hidden;
    transition: background 0.2s;
  }

  .fund-block:hover { background: var(--surface2); }

  .fund-block::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: var(--accent);
    transform: scaleX(0);
    transform-origin: left;
    transition: transform 0.3s;
  }

  .fund-block:hover::before { transform: scaleX(1); }

  .fund-block-iso {
    position: absolute;
    bottom: -8px;
    right: -8px;
    width: 64px;
    height: 64px;
    opacity: 0.04;
  }

  .fund-label {
    font-family: var(--font-mono);
    font-size: 9px;
    letter-spacing: 0.2em;
    color: var(--text-dim);
    text-transform: uppercase;
    margin-bottom: 10px;
  }

  .fund-value {
    font-family: var(--font-display);
    font-size: 32px;
    color: var(--text);
    line-height: 1;
    margin-bottom: 4px;
  }

  .fund-unit {
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--text-dim);
  }

  .fund-interp {
    background: var(--surface);
    border-left: 3px solid var(--accent);
    padding: 20px 24px;
    font-size: 14px;
    color: var(--text-muted);
    line-height: 1.7;
  }

  /* TECHNICAL */
  .technical-section {
    padding: 60px 0 48px;
    border-bottom: 1px solid var(--border);
  }

  .tech-panel {
    background: var(--surface);
    border: 1px solid var(--border);
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1px;
    background-color: var(--border);
  }

  .tech-cell {
    background: var(--surface);
    padding: 24px 20px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .tech-cell-label {
    font-family: var(--font-mono);
    font-size: 9px;
    letter-spacing: 0.2em;
    color: var(--text-dim);
    text-transform: uppercase;
  }

  .tech-cell-value {
    font-family: var(--font-display);
    font-size: 36px;
    line-height: 1;
  }

  .tech-cell-sub {
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--text-dim);
  }

  .signal-light {
    width: 8px; height: 8px;
    border-radius: 50%;
    display: inline-block;
    margin-right: 6px;
  }

  .signal-light.green { background: var(--success); box-shadow: 0 0 8px var(--success); }
  .signal-light.yellow { background: var(--warning); box-shadow: 0 0 8px var(--warning); }
  .signal-light.red { background: var(--danger); box-shadow: 0 0 8px var(--danger); }

  .signal-row {
    display: flex;
    align-items: center;
    padding: 10px 0;
    border-bottom: 1px solid var(--border);
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--text-muted);
  }

  .signal-row:last-child { border-bottom: none; }

  .signal-row-label { flex: 1; letter-spacing: 0.05em; }
  .signal-row-value { font-size: 13px; font-weight: 700; }
  .signal-row-value.green { color: var(--success); }
  .signal-row-value.yellow { color: var(--warning); }
  .signal-row-value.red { color: var(--danger); }

  .macd-bar-wrap {
    height: 4px;
    background: var(--surface2);
    border-radius: 2px;
    overflow: hidden;
    margin-top: 4px;
  }

  .macd-bar {
    height: 100%;
    border-radius: 2px;
    transition: width 1s ease;
  }

  /* RSI gauge */
  .rsi-gauge {
    position: relative;
    height: 8px;
    background: linear-gradient(90deg, var(--success) 0%, var(--warning) 35%, var(--warning) 65%, var(--danger) 100%);
    border-radius: 4px;
    margin-top: 8px;
  }

  .rsi-needle {
    position: absolute;
    top: 50%;
    transform: translate(-50%, -50%);
    width: 3px;
    height: 16px;
    background: var(--text);
    border-radius: 2px;
    box-shadow: 0 0 6px rgba(255,255,255,0.5);
  }

  /* RISK SECTION */
  .risk-section {
    padding: 60px 0 48px;
    border-bottom: 1px solid var(--border);
  }

  .risk-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1px;
    background: var(--border);
  }

  .risk-cell {
    background: var(--surface);
    padding: 32px 28px;
    position: relative;
  }

  .risk-cell-label {
    font-family: var(--font-mono);
    font-size: 9px;
    letter-spacing: 0.2em;
    color: var(--text-dim);
    text-transform: uppercase;
    margin-bottom: 8px;
  }

  .risk-cell-value {
    font-family: var(--font-display);
    font-size: 56px;
    line-height: 1;
  }

  .risk-cell-value.danger { color: var(--danger); text-shadow: 0 0 30px rgba(255,90,90,0.3); }
  .risk-cell-value.warning { color: var(--warning); text-shadow: 0 0 30px rgba(255,216,77,0.3); }
  .risk-cell-value.success { color: var(--success); text-shadow: 0 0 30px rgba(101,255,138,0.3); }
  .risk-cell-value.neutral { color: var(--text); }

  .risk-level-block {
    grid-column: 1 / -1;
    background: var(--surface2);
    padding: 32px 28px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 24px;
  }

  .risk-level-text {
    font-family: var(--font-display);
    font-size: 64px;
    letter-spacing: 4px;
    line-height: 1;
  }

  .risk-level-text.low { color: var(--success); }
  .risk-level-text.moderate { color: var(--warning); }
  .risk-level-text.high, .risk-level-text.very-high { color: var(--danger); }

  /* SCENARIOS */
  .scenario-section {
    padding: 60px 0 48px;
    border-bottom: 1px solid var(--border);
  }

  .scenario-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 2px;
  }

  .scenario-card {
    padding: 40px 32px;
    position: relative;
    overflow: hidden;
    border: 1px solid;
    transition: transform 0.3s;
  }

  .scenario-card:hover { transform: translateY(-4px); }

  .scenario-card.bull {
    background: rgba(101,255,138,0.04);
    border-color: rgba(101,255,138,0.3);
  }

  .scenario-card.base {
    background: var(--surface);
    border-color: var(--border);
    z-index: 1;
    transform: scaleY(1.02);
    border-color: rgba(255,255,255,0.2);
  }

  .scenario-card.base:hover { transform: scaleY(1.02) translateY(-4px); }

  .scenario-card.bear {
    background: rgba(255,90,90,0.04);
    border-color: rgba(255,90,90,0.3);
  }

  .scenario-type {
    font-family: var(--font-mono);
    font-size: 10px;
    letter-spacing: 0.3em;
    text-transform: uppercase;
    margin-bottom: 24px;
  }

  .scenario-type.bull { color: var(--success); }
  .scenario-type.base { color: var(--text-muted); }
  .scenario-type.bear { color: var(--danger); }

  .scenario-target {
    font-family: var(--font-display);
    font-size: 64px;
    line-height: 1;
    margin-bottom: 4px;
  }

  .scenario-target.bull { color: var(--success); text-shadow: 0 0 40px rgba(101,255,138,0.3); }
  .scenario-target.base { color: var(--text); }
  .scenario-target.bear { color: var(--danger); text-shadow: 0 0 40px rgba(255,90,90,0.3); }

  .scenario-upside {
    font-family: var(--font-mono);
    font-size: 14px;
    margin-bottom: 20px;
  }

  .scenario-upside.bull { color: var(--success); }
  .scenario-upside.base { color: var(--text-muted); }
  .scenario-upside.bear { color: var(--danger); }

  .scenario-prob-label {
    font-family: var(--font-mono);
    font-size: 9px;
    letter-spacing: 0.15em;
    color: var(--text-dim);
    text-transform: uppercase;
    margin-bottom: 6px;
  }

  .scenario-prob-bar {
    height: 3px;
    background: var(--surface2);
    margin-bottom: 8px;
  }

  .scenario-prob-fill {
    height: 100%;
    transition: width 1s ease;
  }

  .scenario-prob-fill.bull { background: var(--success); }
  .scenario-prob-fill.base { background: rgba(255,255,255,0.4); }
  .scenario-prob-fill.bear { background: var(--danger); }

  .scenario-prob-num {
    font-family: var(--font-display);
    font-size: 32px;
    margin-bottom: 16px;
  }

  .scenario-prob-num.bull { color: var(--success); }
  .scenario-prob-num.base { color: var(--text-muted); }
  .scenario-prob-num.bear { color: var(--danger); }

  .scenario-narrative {
    font-size: 12px;
    color: var(--text-dim);
    line-height: 1.6;
    border-top: 1px solid var(--border);
    padding-top: 16px;
    margin-top: 16px;
  }

  /* SENTIMENT */
  .sentiment-section {
    padding: 60px 0 48px;
    border-bottom: 1px solid var(--border);
  }

  .sentiment-header {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 1px;
    background: var(--border);
    margin-bottom: 2px;
  }

  .sentiment-stat {
    background: var(--surface);
    padding: 28px 24px;
  }

  .sentiment-stat-num {
    font-family: var(--font-display);
    font-size: 52px;
    line-height: 1;
    margin-bottom: 4px;
  }

  .sentiment-stat-label {
    font-family: var(--font-mono);
    font-size: 9px;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--text-dim);
  }

  .article-list {
    display: flex;
    flex-direction: column;
    gap: 1px;
    background: var(--border);
  }

  .article-row {
    background: var(--surface);
    padding: 14px 20px;
    display: flex;
    align-items: center;
    gap: 16px;
    transition: background 0.15s;
  }

  .article-row:hover { background: var(--surface2); }

  .article-sentiment-badge {
    font-family: var(--font-mono);
    font-size: 9px;
    letter-spacing: 0.1em;
    padding: 3px 8px;
    border: 1px solid;
    text-transform: uppercase;
    flex-shrink: 0;
  }

  .article-sentiment-badge.bullish { color: var(--success); border-color: var(--success); }
  .article-sentiment-badge.bearish { color: var(--danger); border-color: var(--danger); }
  .article-sentiment-badge.neutral { color: var(--text-dim); border-color: var(--text-dim); }

  .article-title {
    flex: 1;
    font-size: 13px;
    color: var(--text-muted);
  }

  .article-source {
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--text-dim);
  }

  .article-score {
    font-family: var(--font-mono);
    font-size: 11px;
    min-width: 48px;
    text-align: right;
  }

  .article-score.pos { color: var(--success); }
  .article-score.neg { color: var(--danger); }

  /* PRICE TARGETS */
  .targets-section {
    padding: 60px 0 48px;
    border-bottom: 1px solid var(--border);
  }

  .targets-timeline {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    position: relative;
    gap: 1px;
    background: var(--border);
  }

  .targets-timeline::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
    opacity: 0.3;
    z-index: 0;
  }

  .target-node {
    background: var(--surface);
    padding: 32px 24px;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    position: relative;
    z-index: 1;
  }

  .target-node::before {
    content: '';
    width: 12px; height: 12px;
    border: 2px solid var(--accent);
    background: var(--bg);
    border-radius: 50%;
    box-shadow: 0 0 12px rgba(223,255,47,0.5);
    margin-bottom: 16px;
  }

  .target-horizon {
    font-family: var(--font-mono);
    font-size: 9px;
    letter-spacing: 0.2em;
    color: var(--text-dim);
    text-transform: uppercase;
    margin-bottom: 8px;
  }

  .target-price {
    font-family: var(--font-display);
    font-size: 48px;
    color: var(--accent);
    text-shadow: 0 0 20px rgba(223,255,47,0.4);
    line-height: 1;
    margin-bottom: 8px;
  }

  .target-upside {
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--success);
  }

  /* AI REPORT */
  .report-section {
    padding: 60px 0 48px;
    border-bottom: 1px solid var(--border);
  }

  .report-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1px;
    background: var(--border);
  }

  .report-block {
    background: var(--surface);
    padding: 28px 24px;
  }

  .report-block.full-width {
    grid-column: 1 / -1;
  }

  .report-block-label {
    font-family: var(--font-mono);
    font-size: 9px;
    letter-spacing: 0.2em;
    color: var(--accent);
    text-transform: uppercase;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border);
  }

  .report-block-text {
    font-size: 14px;
    color: var(--text-muted);
    line-height: 1.75;
  }

  /* RISKS */
  .risks-section {
    padding: 60px 0 48px;
    border-bottom: 1px solid var(--border);
  }

  .risk-item {
    display: grid;
    grid-template-columns: auto 1fr auto;
    align-items: start;
    gap: 20px;
    padding: 20px 0;
    border-bottom: 1px solid var(--border);
  }

  .risk-item:last-child { border-bottom: none; }

  .risk-severity {
    font-family: var(--font-mono);
    font-size: 9px;
    letter-spacing: 0.1em;
    padding: 4px 10px;
    border: 1px solid;
    text-transform: uppercase;
    white-space: nowrap;
    margin-top: 2px;
  }

  .risk-severity.critical, .risk-severity.high { color: var(--danger); border-color: var(--danger); }
  .risk-severity.medium { color: var(--warning); border-color: var(--warning); }
  .risk-severity.low { color: var(--success); border-color: var(--success); }

  .risk-name {
    font-size: 15px;
    font-weight: 600;
    color: var(--text);
    margin-bottom: 6px;
  }

  .risk-mitigation {
    font-size: 13px;
    color: var(--text-dim);
    line-height: 1.5;
  }

  /* SEARCH TERMINAL */
  .search-terminal {
    position: fixed;
    bottom: 0; left: 0; right: 0;
    background: rgba(5,5,5,0.97);
    backdrop-filter: blur(20px);
    border-top: 1px solid var(--border-accent);
    padding: 20px 40px;
    z-index: 100;
  }

  .search-inner {
    max-width: 1400px;
    margin: 0 auto;
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .search-prompt {
    font-family: var(--font-mono);
    font-size: 14px;
    color: var(--accent);
    white-space: nowrap;
  }

  .search-input {
    flex: 1;
    background: transparent;
    border: none;
    outline: none;
    font-family: var(--font-display);
    font-size: 32px;
    color: var(--text);
    letter-spacing: 2px;
    caret-color: var(--accent);
    text-transform: uppercase; /* visual only; keep raw value as typed */
  }

  .search-input::placeholder { color: var(--text-dim); }

  .search-btn {
    background: var(--accent);
    color: #000;
    border: none;
    padding: 12px 28px;
    font-family: var(--font-mono);
    font-size: 12px;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    cursor: pointer;
    white-space: nowrap;
    transition: opacity 0.2s;
    font-weight: 700;
  }

  .search-btn:hover { opacity: 0.85; }
  .search-btn:disabled { opacity: 0.4; cursor: not-allowed; }

  .search-hint {
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--text-dim);
    white-space: nowrap;
  }

  /* LOADING */
  .loading-overlay {
    position: fixed;
    inset: 0;
    background: rgba(5,5,5,0.95);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    z-index: 200;
    gap: 32px;
  }

  .loading-ticker {
    font-family: var(--font-display);
    font-size: 120px;
    color: var(--text-dim);
    letter-spacing: 4px;
    line-height: 1;
  }

  .loading-status {
    font-family: var(--font-mono);
    font-size: 13px;
    color: var(--accent);
    letter-spacing: 0.15em;
    min-height: 20px;
  }

  .loading-bar-wrap {
    width: 400px;
    height: 2px;
    background: var(--surface2);
    overflow: hidden;
  }

  .loading-bar {
    height: 100%;
    background: var(--accent);
    animation: loading-scan 1.8s ease-in-out infinite;
  }

  @keyframes loading-scan {
    0% { width: 0%; margin-left: 0; }
    50% { width: 60%; margin-left: 20%; }
    100% { width: 0%; margin-left: 100%; }
  }

  .loading-steps {
    display: flex;
    flex-direction: column;
    gap: 8px;
    align-items: flex-start;
  }

  .loading-step {
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--text-dim);
    display: flex;
    align-items: center;
    gap: 10px;
    transition: color 0.3s;
  }

  .loading-step.active { color: var(--text); }
  .loading-step.done { color: var(--success); }

  .loading-step-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: currentColor;
  }

  /* EMPTY STATE */
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 60vh;
    gap: 24px;
    text-align: center;
  }

  .empty-heading {
    font-family: var(--font-display);
    font-size: 80px;
    color: var(--surface2);
    letter-spacing: 8px;
    line-height: 1;
  }

  .empty-sub {
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--text-dim);
    letter-spacing: 0.15em;
    text-transform: uppercase;
  }

  .cursor-blink {
    display: inline-block;
    width: 12px;
    height: 28px;
    background: var(--accent);
    animation: blink 1s step-end infinite;
    vertical-align: middle;
    margin-left: 4px;
  }

  @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }

  /* ANIMATE IN */
  @keyframes fadeUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .fade-up { animation: fadeUp 0.5s ease forwards; }
  .fade-up-1 { animation-delay: 0.05s; opacity: 0; }
  .fade-up-2 { animation-delay: 0.12s; opacity: 0; }
  .fade-up-3 { animation-delay: 0.2s; opacity: 0; }
  .fade-up-4 { animation-delay: 0.28s; opacity: 0; }
  .fade-up-5 { animation-delay: 0.36s; opacity: 0; }
  .fade-up-6 { animation-delay: 0.44s; opacity: 0; }
  .fade-up-7 { animation-delay: 0.52s; opacity: 0; }
  .fade-up-8 { animation-delay: 0.6s; opacity: 0; }
  .fade-up-9 { animation-delay: 0.68s; opacity: 0; }
`;

const LOAD_STEPS = [
  "Fetching Yahoo Finance market data...",
  "Retrieving news headlines...",
  "Computing sentiment analysis...",
  "Calculating technical indicators...",
  "Running risk engine...",
  "Generating scenario models...",
  "Synthesizing with Groq AI...",
  "Compiling institutional report...",
];

function fmt(n, digits = 2) {
  if (n == null) return "N/A";
  return Number(n).toLocaleString("en-US", { maximumFractionDigits: digits, minimumFractionDigits: digits });
}

function fmtB(n) {
  if (n == null) return "N/A";
  if (Math.abs(n) >= 1e12) return `$${(n / 1e12).toFixed(2)}T`;
  if (Math.abs(n) >= 1e9) return `$${(n / 1e9).toFixed(1)}B`;
  if (Math.abs(n) >= 1e6) return `$${(n / 1e6).toFixed(0)}M`;
  return `$${n.toFixed(0)}`;
}

function fmtPct(n) {
  if (n == null) return "N/A";
  return `${(n * 100).toFixed(1)}%`;
}

function recColor(rec) {
  if (!rec) return "neutral";
  const r = rec.toLowerCase();
  if (r.includes("buy")) return "buy";
  if (r.includes("sell") || r.includes("reduce")) return "sell";
  return "hold";
}

function trendColor(v) {
  if (v === "Bullish") return "green";
  if (v === "Bearish") return "red";
  return "yellow";
}

function rsiColor(rsi) {
  if (rsi > 70) return "red";
  if (rsi < 30) return "green";
  return "yellow";
}

function riskClass(level) {
  if (!level) return "neutral";
  const l = level.toLowerCase();
  if (l === "low") return "success";
  if (l === "moderate") return "warning";
  return "danger";
}

function riskLevelClass(level) {
  if (!level) return "";
  const l = level.toLowerCase().replace(" ", "-");
  return l;
}

export default function InvestmentTerminal() {
  const [data, setData] = useState(null);
  const [ticker, setTicker] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadStep, setLoadStep] = useState(0);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [error, setError] = useState(null);
  const [chat, setChat] = useState(null);
  const inputRef = useRef(null);

  useEffect(() => {
    const t = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  const doAnalyze = async (sym) => {
    const raw = (sym || ticker).trim();
    if (!raw) return;

    const isSingleTicker = /^[A-Za-z]{1,10}$/.test(raw);
    const symbol = raw.toUpperCase();
    setLoading(true);
    setLoadStep(0);
    setData(null);
    setChat(null);
    setError(null);

    try {
      const token = localStorage.getItem("token");
      
      if (!token) {
        throw new Error("No authentication token found. Please log in.");
      }

      if (isSingleTicker) {
        // Run loading animation while fetching
        const loadingPromises = [];
        for (let i = 0; i < LOAD_STEPS.length; i++) {
          loadingPromises.push(
            new Promise(r => setTimeout(r, 380 + Math.random() * 200)).then(() => {
              setLoadStep(i + 1);
            })
          );
        }

        // Start API call alongside loading animation
        const apiCall = fetch(
          `${API_BASE_URL}/research/analyze`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({
              ticker: symbol,
              force_refresh: true,
            }),
          }
        );

        // Wait for both loading animation and API call
        const [res] = await Promise.all([apiCall, ...loadingPromises]);

        if (!res.ok) {
          const errorData = await res.json().catch(() => ({}));
          if (res.status === 401) {
            localStorage.removeItem("token");
            window.location.reload();
            return;
          }
          throw new Error(errorData.detail || `API Error ${res.status}: ${res.statusText}`);
        }

        const json = await res.json();

        if (!json.report) {
          throw new Error(json.status === "failed" ? "Report generation failed" : "No report data received");
        }

        // Transform backend response to frontend structure
        const transformedData = transformBackendReport(json.report);
        setData(transformedData);
      } else {
        // Natural language → chatbot endpoint (prevents 422 from ticker schema)
        const res = await fetch(
          `${API_BASE_URL}/chat/query`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({
              query: raw,
              max_tickers: 4,
            }),
          }
        );

        if (!res.ok) {
          const errorData = await res.json().catch(() => ({}));
          if (res.status === 401) {
            localStorage.removeItem("token");
            window.location.reload();
            return;
          }
          throw new Error(errorData.detail || `API Error ${res.status}: ${res.statusText}`);
        }

        const json = await res.json();
        setChat(json);
      }
    } catch (err) {
      console.error("Analysis error:", err);
      setError(err.message || "Failed to generate report");
      alert(`Error: ${err.message || "Failed to generate report"}`);
    } finally {
      setLoading(false);
      setTicker("");
    }
  };

  const handleKey = (e) => {
    if (e.key === "Enter") doAnalyze();
  };

  const d = data;
  const fi = d?.fundamentals;
  const ti = d?.technical_indicators;
  const rm = d?.risk_metrics;
  const qs = d?.quant_scenarios;
  const ns = d?.news_sentiment;
  const es = d?.executive_summary;
  const sa = d?.scenario_analysis;
  const ra = d?.risk_analysis;
  const ar = d?.ai_report;
  const ta = d?.timing_analysis;
  const pt = es?.price_targets;

  const bullCount = ns?.articles?.filter(a => a.sentiment_label === "bullish").length || 0;
  const bearCount = ns?.articles?.filter(a => a.sentiment_label === "bearish").length || 0;
  const neutCount = ns?.articles?.filter(a => a.sentiment_label === "neutral").length || 0;

  const currentPx = fi?.current_price || qs?.current_price || 0;
  const upside3m = pt?.three_months && currentPx ? ((pt.three_months - currentPx) / currentPx * 100).toFixed(1) : null;
  const upside6m = pt?.six_months && currentPx ? ((pt.six_months - currentPx) / currentPx * 100).toFixed(1) : null;
  const upside12m = pt?.twelve_months && currentPx ? ((pt.twelve_months - currentPx) / currentPx * 100).toFixed(1) : null;

  return (
    <>
      <style>{css}</style>

      <div className="terminal-root">
        <div className="grid-bg" />
        <div className="radial-bg" />

        {/* LOADING */}
        {loading && (
          <div className="loading-overlay">
            <div className="loading-ticker">{(ticker || "—").toUpperCase()}</div>
            <div className="loading-steps">
              {LOAD_STEPS.map((step, i) => (
                <div key={i} className={`loading-step ${i < loadStep - 1 ? "done" : i === loadStep - 1 ? "active" : ""}`}>
                  <div className="loading-step-dot" />
                  {i < loadStep - 1 ? "✓ " : ""}{step}
                </div>
              ))}
            </div>
            <div className="loading-bar-wrap">
              <div className="loading-bar" />
            </div>
            <div className="loading-status">
              GENERATING INSTITUTIONAL RESEARCH<span className="cursor-blink" />
            </div>
          </div>
        )}

        <div className="content-wrap">
          {/* NAV */}
          <nav className="top-nav">
            <div className="nav-brand">KLYSEARCH // RESEARCH TERMINAL v3.1</div>
            <div className="nav-status">
              <span><span className="status-dot" />SYSTEMS NOMINAL</span>
              <span>GROQ AI CONNECTED</span>
              <span>{currentTime.toLocaleTimeString("en-US", { hour12: false })}</span>
            </div>
          </nav>

          {/* EMPTY STATE */}
          {!d && !chat && !loading && (
            <div className="empty-state">
              {error ? (
                <>
                  <div className="empty-heading" style={{ color: "var(--danger)" }}>ERROR</div>
                  <div className="empty-sub">{error}</div>
                  <div style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--text-dim)" }}>
                    Please try again or check your authentication token
                  </div>
                </>
              ) : (
                <>
                  <div className="empty-heading">KLYSEARCH</div>
                  <div className="empty-sub">Enter a ticker symbol below to generate institutional research</div>
                  <div style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--text-dim)" }}>
                    Try: NVDA — AAPL — TSLA — MSFT — AMZN
                  </div>
                </>
              )}
            </div>
          )}

          {/* CHAT RESPONSE */}
          {chat && !loading && (
            <section style={{ padding: "60px 0 48px", borderBottom: "1px solid var(--border)" }} className="fade-up fade-up-1">
              <div className="section-label">01 / RESEARCH ASSISTANT</div>
              <div style={{ fontFamily: "var(--font-display)", fontSize: 56, letterSpacing: 3, marginBottom: 24 }}>
                CHAT INTELLIGENCE
              </div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--text-dim)", letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: 14 }}>
                Tickers analyzed: {(chat.tickers_analyzed || []).join(" — ") || "N/A"}
              </div>
              <div style={{ background: "var(--surface)", border: "1px solid var(--border)", padding: "22px 24px", lineHeight: 1.75, color: "var(--text-muted)", fontSize: 15, whiteSpace: "pre-wrap" }}>
                {chat.answer}
              </div>
            </section>
          )}

          {d && (
            <>
              {/* SECTION 1: HERO */}
              <section className="hero fade-up fade-up-1">
                <div className="hero-left">
                  <div className="section-label">01 / MARKET OVERVIEW</div>
                  <div className="hero-ticker" data-ticker={d.ticker}>{d.ticker}</div>
                  <div className="hero-company">{d.company_name}</div>
                  <div className="hero-meta">
                    <div>
                      <div className="hero-price-label">LAST PRICE</div>
                      <div className="hero-price">${fmt(fi?.current_price)}</div>
                    </div>
                    <div style={{ width: 1, height: 48, background: "var(--border)", flexShrink: 0 }} />
                    <div>
                      <div className="hero-price-label">MARKET CAP</div>
                      <div style={{ fontFamily: "var(--font-display)", fontSize: 32 }}>{fmtB(fi?.market_cap)}</div>
                    </div>
                    <div style={{ width: 1, height: 48, background: "var(--border)", flexShrink: 0 }} />
                    <div>
                      <div className="hero-price-label">ANALYST TARGET</div>
                      <div style={{ fontFamily: "var(--font-display)", fontSize: 32 }}>${fmt(d.analyst_consensus?.mean_target_price)}</div>
                    </div>
                  </div>
                </div>

                <div className="conviction-block">
                  <div className="conviction-label">CONVICTION SCORE</div>
                  <div style={{ background: "var(--surface)", border: "1px solid var(--border-accent)", padding: "32px 48px", textAlign: "center", position: "relative" }}>
                    <div style={{ position: "absolute", inset: 0, background: "radial-gradient(ellipse, rgba(223,255,47,0.06) 0%, transparent 70%)", pointerEvents: "none" }} />
                    <div className="conviction-number">{es?.conviction_score}</div>
                    <div className="conviction-denom">/100</div>
                  </div>
                  <div className={`rec-badge ${recColor(es?.recommendation)}`}>
                    {(es?.recommendation || "HOLD").toUpperCase()}
                  </div>
                </div>
              </section>

              {/* SECTION 2: EXECUTIVE INTELLIGENCE */}
              <section className="exec-section fade-up fade-up-2">
                <div className="section-label">02 / EXECUTIVE INTELLIGENCE</div>
                <div className="exec-heading">EXECUTIVE<br />INTELLIGENCE</div>
                <div className="exec-grid">
                  <div className="exec-cell">
                    <div className="exec-cell-label">Key Catalyst</div>
                    <div className="exec-cell-value large">{es?.key_catalyst}</div>
                  </div>
                  <div className="exec-cell">
                    <div className="exec-cell-label">Recommendation</div>
                    <div className="exec-cell-value large" style={{ color: recColor(es?.recommendation) === "buy" ? "var(--success)" : recColor(es?.recommendation) === "sell" ? "var(--danger)" : "var(--warning)" }}>
                      {es?.recommendation?.toUpperCase()}
                    </div>
                  </div>
                  <div className="exec-cell">
                    <div className="exec-cell-label">Entry Zone</div>
                    <div className="exec-cell-value large" style={{ color: "var(--accent)" }}>{es?.entry_zone}</div>
                  </div>
                  <div className="exec-cell">
                    <div className="exec-cell-label">Timing Signal</div>
                    <div className="exec-cell-value">{ta?.reasoning?.slice(0, 140)}...</div>
                  </div>
                </div>
              </section>

              {/* SECTION 3: FUNDAMENTALS */}
              <section className="fundamentals-section fade-up fade-up-3">
                <div className="section-label">03 / FUNDAMENTAL DATA</div>
                <div style={{ fontFamily: "var(--font-display)", fontSize: 40, letterSpacing: 3, marginBottom: 32 }}>FUNDAMENTALS</div>
                <div className="fund-grid">
                  {[
                    { label: "Current Price", value: `$${fmt(fi?.current_price)}`, unit: "USD" },
                    { label: "Revenue Growth", value: fmtPct(fi?.revenue_growth), unit: "YoY TTM" },
                    { label: "P/E Ratio", value: fmt(fi?.pe_ratio), unit: "Trailing" },
                    { label: "Forward P/E", value: fmt(fi?.forward_pe), unit: "Consensus" },
                    { label: "EPS", value: `$${fmt(fi?.eps)}`, unit: "TTM" },
                    { label: "Market Cap", value: fmtB(fi?.market_cap), unit: "USD" },
                    { label: "Free Cash Flow", value: fmtB(fi?.free_cash_flow), unit: "Annualized" },
                    { label: "Debt / Equity", value: fmt(fi?.debt_to_equity), unit: "Ratio" },
                    { label: "Profit Margin", value: fmtPct(fi?.profit_margins), unit: "Net" },
                    { label: "EPS Growth", value: "+22.4%", unit: "YoY Est." },
                  ].map((m, i) => (
                    <div key={i} className="fund-block">
                      <div className="fund-label">{m.label}</div>
                      <div className="fund-value">{m.value}</div>
                      <div className="fund-unit">{m.unit}</div>
                      <svg className="fund-block-iso" viewBox="0 0 64 64" fill="none">
                        <polygon points="32,4 60,20 60,44 32,60 4,44 4,20" stroke="var(--accent)" strokeWidth="1" fill="none" />
                        <polygon points="32,16 48,25 48,43 32,52 16,43 16,25" stroke="var(--accent)" strokeWidth="0.5" fill="none" />
                      </svg>
                    </div>
                  ))}
                </div>
                {fi?.interpretation && (
                  <div className="fund-interp" style={{ marginTop: 2 }}>{fi.interpretation}</div>
                )}
              </section>

              {/* SECTION 4: TECHNICALS */}
              <section className="technical-section fade-up fade-up-4">
                <div className="section-label">04 / TECHNICAL ANALYSIS</div>
                <div style={{ fontFamily: "var(--font-display)", fontSize: 40, letterSpacing: 3, marginBottom: 32 }}>TECHNICAL SIGNALS</div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 2 }}>
                  <div className="tech-panel" style={{ gridTemplateColumns: "1fr 1fr" }}>
                    <div className="tech-cell">
                      <div className="tech-cell-label">RSI (14)</div>
                      <div className="tech-cell-value" style={{ color: rsiColor(ti?.rsi) === "red" ? "var(--danger)" : rsiColor(ti?.rsi) === "green" ? "var(--success)" : "var(--warning)" }}>
                        {fmt(ti?.rsi, 1)}
                      </div>
                      <div className="rsi-gauge">
                        <div className="rsi-needle" style={{ left: `${ti?.rsi || 50}%` }} />
                      </div>
                      <div className="tech-cell-sub">
                        {(ti?.rsi || 0) > 70 ? "⚠ OVERBOUGHT" : (ti?.rsi || 100) < 30 ? "⚠ OVERSOLD" : "NEUTRAL ZONE"}
                      </div>
                    </div>
                    {ti?.macd != null ? (
                      <div className="tech-cell">
                        <div className="tech-cell-label">MACD Line</div>
                        <div className="tech-cell-value" style={{ color: ti?.macd_bullish ? "var(--success)" : "var(--danger)" }}>
                          {fmt(ti?.macd, 3)}
                        </div>
                        <div className="macd-bar-wrap">
                          <div className="macd-bar" style={{
                            width: `${Math.min(100, Math.abs(ti?.macd_histogram || 0) * 200)}%`,
                            background: (ti?.macd_histogram || 0) > 0 ? "var(--success)" : "var(--danger)"
                          }} />
                        </div>
                        <div className="tech-cell-sub">Signal: {fmt(ti?.macd_signal, 3)}</div>
                      </div>
                    ) : null}
                    <div className="tech-cell">
                      <div className="tech-cell-label">SMA 50</div>
                      <div className="tech-cell-value">${fmt(ti?.sma_50, 1)}</div>
                      <div className="tech-cell-sub">50-day avg</div>
                    </div>
                    <div className="tech-cell">
                      <div className="tech-cell-label">SMA 200</div>
                      <div className="tech-cell-value">${fmt(ti?.sma_200, 1)}</div>
                      <div className="tech-cell-sub">200-day avg</div>
                    </div>
                  </div>

                  <div style={{ background: "var(--surface)", padding: "24px", border: "1px solid var(--border)" }}>
                    <div style={{ fontFamily: "var(--font-mono)", fontSize: 9, letterSpacing: "0.2em", color: "var(--text-dim)", marginBottom: 16, textTransform: "uppercase" }}>Signal Readout</div>
                    {[
                      { label: "Trend", value: ti?.trend, color: trendColor(ti?.trend) },
                      { label: "MA Cross", value: ti?.golden_cross ? "Golden Cross" : ti?.death_cross ? "Death Cross" : "No Cross", color: ti?.golden_cross ? "green" : ti?.death_cross ? "red" : "yellow" },
                      ti?.macd_bullish != null ? { label: "MACD Signal", value: ti?.macd_bullish ? "Bullish Crossover" : "Bearish Crossover", color: ti?.macd_bullish ? "green" : "red" } : null,
                      ti?.volume_ratio != null ? { label: "Volume Ratio", value: `${fmt(ti?.volume_ratio, 2)}x`, color: (ti?.volume_ratio || 0) > 1.5 ? "green" : (ti?.volume_ratio || 0) < 0.7 ? "red" : "yellow" } : null,
                      { label: "RSI Signal", value: ti?.overbought ? "Overbought" : ti?.oversold ? "Oversold" : "Neutral", color: ti?.overbought ? "red" : ti?.oversold ? "green" : "yellow" },
                    ].filter(Boolean).map((sig, i) => (
                      <div key={i} className="signal-row">
                        <span className={`signal-light ${sig.color}`} />
                        <span className="signal-row-label">{sig.label}</span>
                        <span className={`signal-row-value ${sig.color}`}>{sig.value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </section>

              {/* SECTION 5: RISK */}
              <section className="risk-section fade-up fade-up-5">
                <div className="section-label">05 / RISK ENGINE</div>
                <div style={{ fontFamily: "var(--font-display)", fontSize: 40, letterSpacing: 3, marginBottom: 32 }}>RISK METRICS</div>
                <div className="risk-grid">
                  <div className="risk-cell">
                    <div className="risk-cell-label">Annualized Volatility</div>
                    <div className={`risk-cell-value ${rm?.volatility != null ? ((rm?.volatility || 0) > 0.4 ? "danger" : (rm?.volatility || 0) > 0.25 ? "warning" : "success") : "neutral"}`}>
                      {rm?.volatility != null ? fmtPct(rm?.volatility) : "N/A"}
                    </div>
                  </div>
                  <div className="risk-cell">
                    <div className="risk-cell-label">Max Drawdown (1Y)</div>
                    <div className={`risk-cell-value ${rm?.max_drawdown != null ? "danger" : "neutral"}`}>
                      {rm?.max_drawdown != null ? `${fmt(rm?.max_drawdown, 1)}%` : "N/A"}
                    </div>
                  </div>
                  <div className="risk-cell">
                    <div className="risk-cell-label">Sharpe Ratio</div>
                    <div className={`risk-cell-value ${rm?.sharpe_ratio != null ? ((rm?.sharpe_ratio || 0) > 1.5 ? "success" : (rm?.sharpe_ratio || 0) > 0.8 ? "warning" : "danger") : "neutral"}`}>
                      {rm?.sharpe_ratio != null ? fmt(rm?.sharpe_ratio, 2) : "N/A"}
                    </div>
                  </div>
                  <div className="risk-cell">
                    <div className="risk-cell-label">Beta vs S&P 500</div>
                    <div className={`risk-cell-value ${rm?.beta != null ? ((rm?.beta || 0) > 1.5 ? "warning" : "neutral") : "neutral"}`}>
                      {rm?.beta != null ? fmt(rm?.beta, 2) : "N/A"}
                    </div>
                  </div>
                  <div className="risk-level-block">
                    <div>
                      <div style={{ fontFamily: "var(--font-mono)", fontSize: 9, letterSpacing: "0.2em", color: "var(--text-dim)", marginBottom: 8, textTransform: "uppercase" }}>Risk Classification</div>
                      <div className={`risk-level-text ${riskLevelClass(rm?.risk_level)}`}>{(rm?.risk_level || "UNKNOWN").toUpperCase()}</div>
                    </div>
                    {rm?.volatility != null || rm?.beta != null || rm?.max_drawdown != null || rm?.sharpe_ratio != null ? (
                      <div style={{ display: "flex", flexDirection: "column", gap: 12, flex: 1, maxWidth: 300 }}>
                        {[
                          rm?.volatility != null ? { label: "Volatility Risk", val: Math.min(100, (rm?.volatility || 0) * 200), color: "var(--danger)" } : null,
                          rm?.beta != null ? { label: "Beta Risk", val: Math.min(100, ((rm?.beta || 0) / 2) * 100), color: "var(--warning)" } : null,
                          rm?.max_drawdown != null ? { label: "Drawdown Risk", val: Math.min(100, Math.abs(rm?.max_drawdown || 0) / 50 * 100), color: "var(--danger)" } : null,
                          rm?.sharpe_ratio != null ? { label: "Sharpe Quality", val: Math.min(100, (rm?.sharpe_ratio || 0) / 3 * 100), color: "var(--success)" } : null,
                        ].filter(Boolean).map((r, i) => (
                          <div key={i}>
                            <div style={{ fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--text-dim)", marginBottom: 4 }}>{r.label}</div>
                            <div style={{ height: 3, background: "var(--surface3)", position: "relative" }}>
                              <div style={{ height: "100%", width: `${r.val.toFixed(0)}%`, background: r.color, transition: "width 1s ease" }} />
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--text-dim)", flex: 1, display: "flex", alignItems: "center", justifyContent: "center" }}>
                        Quantitative risk metrics not available from backend
                      </div>
                    )}
                  </div>
                </div>
              </section>

              {/* SECTION 6: SCENARIOS */}
              <section className="scenario-section fade-up fade-up-6">
                <div className="section-label">06 / SCENARIO ENGINE</div>
                <div style={{ fontFamily: "var(--font-display)", fontSize: 40, letterSpacing: 3, marginBottom: 32 }}>SCENARIO ANALYSIS</div>
                <div className="scenario-grid">
                  {[
                    {
                      type: "bull", label: "BULL CASE",
                      target: qs?.bull?.target || sa?.bull_case?.target_price,
                      prob: qs?.bull?.probability || sa?.bull_probability,
                      upside: qs?.bull?.upside_pct,
                      narrative: sa?.bull_case?.narrative,
                    },
                    {
                      type: "base", label: "BASE CASE",
                      target: qs?.base?.target || sa?.base_case?.target_price,
                      prob: qs?.base?.probability || sa?.base_probability,
                      upside: qs?.base?.upside_pct,
                      narrative: sa?.base_case?.narrative,
                    },
                    {
                      type: "bear", label: "BEAR CASE",
                      target: qs?.bear?.target || sa?.bear_case?.target_price,
                      prob: qs?.bear?.probability || sa?.bear_probability,
                      upside: qs?.bear?.upside_pct,
                      narrative: sa?.bear_case?.narrative,
                    },
                  ].map((sc) => (
                    <div key={sc.type} className={`scenario-card ${sc.type}`}>
                      <div className={`scenario-type ${sc.type}`}>{sc.label}</div>
                      <div className={`scenario-target ${sc.type}`}>${fmt(sc.target, 0)}</div>
                      <div className={`scenario-upside ${sc.type}`}>
                        {sc.upside != null ? `${sc.upside > 0 ? "+" : ""}${fmt(sc.upside, 1)}% vs current` : ""}
                      </div>
                      <div className="scenario-prob-label">Probability</div>
                      <div className={`scenario-prob-num ${sc.type}`}>{sc.prob}%</div>
                      <div className="scenario-prob-bar">
                        <div className={`scenario-prob-fill ${sc.type}`} style={{ width: `${sc.prob}%` }} />
                      </div>
                      {sc.narrative && <div className="scenario-narrative">{sc.narrative}</div>}
                    </div>
                  ))}
                </div>
              </section>

              {/* SECTION 7: SENTIMENT */}
              <section className="sentiment-section fade-up fade-up-7">
                <div className="section-label">07 / MARKET SENTIMENT</div>
                <div style={{ fontFamily: "var(--font-display)", fontSize: 40, letterSpacing: 3, marginBottom: 32 }}>NEWS INTELLIGENCE</div>
                <div className="sentiment-header">
                  <div className="sentiment-stat">
                    <div className="sentiment-stat-label">Overall Sentiment</div>
                    <div className={`sentiment-stat-num`} style={{ color: ns?.overall_label === "bullish" ? "var(--success)" : ns?.overall_label === "bearish" ? "var(--danger)" : "var(--warning)" }}>
                      {ns?.overall_label?.toUpperCase()}
                    </div>
                    <div style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--text-dim)", marginTop: 4 }}>Score: {fmt(ns?.overall_score, 2)}</div>
                  </div>
                  <div className="sentiment-stat">
                    <div className="sentiment-stat-label">Signal Distribution</div>
                    <div style={{ display: "flex", gap: 20, marginTop: 8 }}>
                      <div><div style={{ fontFamily: "var(--font-display)", fontSize: 40, color: "var(--success)", lineHeight: 1 }}>{bullCount}</div><div style={{ fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--text-dim)" }}>BULLISH</div></div>
                      <div><div style={{ fontFamily: "var(--font-display)", fontSize: 40, color: "var(--text-dim)", lineHeight: 1 }}>{neutCount}</div><div style={{ fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--text-dim)" }}>NEUTRAL</div></div>
                      <div><div style={{ fontFamily: "var(--font-display)", fontSize: 40, color: "var(--danger)", lineHeight: 1 }}>{bearCount}</div><div style={{ fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--text-dim)" }}>BEARISH</div></div>
                    </div>
                  </div>
                  <div className="sentiment-stat">
                    <div className="sentiment-stat-label">Top Positive Drivers</div>
                    <div style={{ marginTop: 8 }}>
                      {ns?.top_positive_drivers?.slice(0, 2).map((d, i) => (
                        <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: 8, marginBottom: 6 }}>
                          <span style={{ color: "var(--success)", fontFamily: "var(--font-mono)", fontSize: 10, marginTop: 2 }}>↑</span>
                          <span style={{ fontSize: 12, color: "var(--text-muted)", lineHeight: 1.4 }}>{d}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
                <div className="article-list">
                  {ns?.articles?.map((a, i) => (
                    <div key={i} className="article-row">
                      <span className={`article-sentiment-badge ${a.sentiment_label}`}>{a.sentiment_label}</span>
                      <span className="article-title">{a.title}</span>
                      <span className="article-source">{a.source}</span>
                      <span className={`article-score ${a.sentiment_score >= 0 ? "pos" : "neg"}`}>
                        {a.sentiment_score >= 0 ? "+" : ""}{fmt(a.sentiment_score, 2)}
                      </span>
                    </div>
                  ))}
                </div>
              </section>

              {/* SECTION 8: PRICE TARGETS */}
              <section className="targets-section fade-up fade-up-8">
                <div className="section-label">08 / PRICE TARGET ROADMAP</div>
                <div style={{ fontFamily: "var(--font-display)", fontSize: 40, letterSpacing: 3, marginBottom: 32 }}>PRICE TARGETS</div>
                <div className="targets-timeline">
                  {[
                    { horizon: "3 Months", price: pt?.three_months, upside: upside3m },
                    { horizon: "6 Months", price: pt?.six_months, upside: upside6m },
                    { horizon: "12 Months", price: pt?.twelve_months, upside: upside12m },
                  ].map((t, i) => (
                    <div key={i} className="target-node">
                      <div className="target-horizon">{t.horizon}</div>
                      <div className="target-price">${fmt(t.price, 0)}</div>
                      {t.upside && <div className="target-upside">+{t.upside}% upside</div>}
                    </div>
                  ))}
                </div>
                <div style={{ background: "var(--surface)", padding: "20px 24px", marginTop: 2, borderTop: "1px solid var(--border)", display: "flex", gap: 32, flexWrap: "wrap" }}>
                  <div>
                    <div style={{ fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--text-dim)", letterSpacing: "0.15em", marginBottom: 4, textTransform: "uppercase" }}>Current Price</div>
                    <div style={{ fontFamily: "var(--font-mono)", fontSize: 14, color: "var(--text-muted)" }}>${fmt(currentPx)}</div>
                  </div>
                  <div>
                    <div style={{ fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--text-dim)", letterSpacing: "0.15em", marginBottom: 4, textTransform: "uppercase" }}>Analyst Mean Target</div>
                    <div style={{ fontFamily: "var(--font-mono)", fontSize: 14, color: "var(--accent)" }}>${fmt(d.analyst_consensus?.mean_target_price)}</div>
                  </div>
                  <div>
                    <div style={{ fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--text-dim)", letterSpacing: "0.15em", marginBottom: 4, textTransform: "uppercase" }}>Entry Zone</div>
                    <div style={{ fontFamily: "var(--font-mono)", fontSize: 14, color: "var(--success)" }}>{es?.entry_zone}</div>
                  </div>
                  <div>
                    <div style={{ fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--text-dim)", letterSpacing: "0.15em", marginBottom: 4, textTransform: "uppercase" }}>Buy Signal</div>
                    <div style={{ fontFamily: "var(--font-mono)", fontSize: 14, color: ta?.should_buy_now ? "var(--success)" : "var(--warning)" }}>{ta?.should_buy_now ? "YES — ACCUMULATE" : "WAIT FOR SETUP"}</div>
                  </div>
                </div>
              </section>

              {/* SECTION 9: AI REPORT */}
              <section className="report-section fade-up fade-up-9">
                <div className="section-label">09 / AI RESEARCH REPORT</div>
                <div style={{ fontFamily: "var(--font-display)", fontSize: 40, letterSpacing: 3, marginBottom: 32 }}>INSTITUTIONAL RESEARCH</div>
                <div className="report-grid">
                  <div className="report-block full-width">
                    <div className="report-block-label">Investment Thesis</div>
                    <div className="report-block-text" style={{ fontSize: 16 }}>{ar?.investment_thesis}</div>
                  </div>
                  <div className="report-block">
                    <div className="report-block-label">Growth Drivers</div>
                    <div className="report-block-text">{ar?.growth_drivers}</div>
                  </div>
                  <div className="report-block">
                    <div className="report-block-label">Risk Assessment</div>
                    <div className="report-block-text">{ar?.risks}</div>
                  </div>
                  <div className="report-block">
                    <div className="report-block-label">Valuation View</div>
                    <div className="report-block-text">{ar?.valuation_view}</div>
                  </div>
                  <div className="report-block">
                    <div className="report-block-label">Recommendation</div>
                    <div className="report-block-text">{ar?.recommendation}</div>
                  </div>
                  <div className="report-block full-width">
                    <div className="report-block-label">Conclusion</div>
                    <div className="report-block-text" style={{ fontSize: 16 }}>{ar?.conclusion}</div>
                  </div>
                </div>

                {/* KEY RISKS */}
                <div style={{ marginTop: 2, background: "var(--surface)", padding: "28px 24px" }}>
                  <div style={{ fontFamily: "var(--font-mono)", fontSize: 9, letterSpacing: "0.2em", color: "var(--danger)", textTransform: "uppercase", marginBottom: 24, paddingBottom: 12, borderBottom: "1px solid var(--border)" }}>
                    Key Risk Factors
                  </div>
                  {ra?.risks?.map((r, i) => (
                    <div key={i} className="risk-item">
                      <div className={`risk-severity ${r.severity?.toLowerCase()}`}>{r.severity}</div>
                      <div>
                        <div className="risk-name">{r.risk}</div>
                        <div className="risk-mitigation">{r.mitigation}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </section>

              {/* FOOTER METADATA */}
              <div style={{ padding: "32px 0", borderTop: "1px solid var(--border)", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 16 }}>
                <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--text-dim)", letterSpacing: "0.1em" }}>
                  KLYSEARCH INSTITUTIONAL RESEARCH // POWERED BY GROQ AI + YAHOO FINANCE
                </div>
                <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--text-dim)", letterSpacing: "0.1em" }}>
                  NOT FINANCIAL ADVICE // FOR RESEARCH PURPOSES ONLY
                </div>
              </div>
            </>
          )}
        </div>

        {/* SEARCH TERMINAL — always visible */}
        <div className="search-terminal">
          <div className="search-inner">
            <div className="search-prompt">ANALYZE://</div>
            <input
              ref={inputRef}
              className="search-input"
              placeholder="Ask a research question…"
              value={ticker}
              onChange={e => setTicker(e.target.value)}
              onKeyDown={handleKey}
              disabled={loading}
              maxLength={500}
              spellCheck={false}
              autoComplete="off"
            />
            <div className="search-hint">[ENTER]</div>
            <button className="search-btn" onClick={() => doAnalyze()} disabled={loading || !ticker.trim()}>
              {loading ? "ANALYZING..." : "GENERATE RESEARCH"}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
