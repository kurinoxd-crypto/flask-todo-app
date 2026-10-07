"""
Generates a professional Selenium test report dashboard.
Run after pytest: python generate_report.py
"""

import json
import os
import sys
from datetime import datetime

RESULTS_FILE = "test_results.json"
REPORT_FILE  = "selenium_report.html"


def load_results():
    if not os.path.exists(RESULTS_FILE):
        return []
    with open(RESULTS_FILE) as f:
        return json.load(f)


def build_html(results):
    total    = len(results)
    passed   = sum(1 for r in results if r["status"] == "PASSED")
    failed   = sum(1 for r in results if r["status"] == "FAILED")
    duration = sum(r["duration"] for r in results)
    pct      = round((passed / total * 100) if total else 0, 1)
    now      = datetime.now().strftime("%d %b %Y  %H:%M:%S")

    rows = ""
    for i, r in enumerate(results):
        status_class = "pass" if r["status"] == "PASSED" else "fail"
        status_icon  = "✓" if r["status"] == "PASSED" else "✗"
        err_row = ""
        if r.get("error"):
            err_row = f'<tr class="err-row"><td colspan="4"><pre>{r["error"]}</pre></td></tr>'
        rows += f"""
        <tr class="{status_class}-row">
            <td class="num">{i+1}</td>
            <td class="test-name">{r['name']}</td>
            <td class="test-class">{r['class']}</td>
            <td class="dur">{r['duration']:.2f}s</td>
            <td><span class="badge {status_class}">{status_icon} {r['status']}</span></td>
        </tr>{err_row}"""

    # Build bar chart data
    bar_segments = ""
    for r in results:
        w = round(100 / total, 1)
        cls = "bar-pass" if r["status"] == "PASSED" else "bar-fail"
        bar_segments += f'<div class="bar-seg {cls}" style="width:{w}%" title="{r["name"]}"></div>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Selenium Test Report</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', sans-serif; background: #0f1117; color: #e2e8f0; min-height: 100vh; }}

  header {{
    background: linear-gradient(135deg, #1a1f2e 0%, #16213e 100%);
    padding: 24px 40px;
    border-bottom: 1px solid #2d3748;
    display: flex; align-items: center; gap: 16px;
  }}
  header .logo {{ font-size: 28px; font-weight: 700; color: #63b3ed; letter-spacing: -0.5px; }}
  header .subtitle {{ color: #718096; font-size: 14px; margin-top: 4px; }}
  header .timestamp {{ margin-left: auto; color: #718096; font-size: 13px; }}

  .container {{ max-width: 1200px; margin: 0 auto; padding: 32px 24px; }}

  .cards {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 32px; }}
  .card {{
    background: #1a1f2e; border-radius: 12px; padding: 24px;
    border: 1px solid #2d3748; position: relative; overflow: hidden;
  }}
  .card::before {{
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
  }}
  .card.total::before  {{ background: #63b3ed; }}
  .card.passed::before {{ background: #48bb78; }}
  .card.failed::before {{ background: #fc8181; }}
  .card.time::before   {{ background: #ed8936; }}
  .card .label {{ font-size: 12px; color: #718096; text-transform: uppercase; letter-spacing: 1px; }}
  .card .value {{ font-size: 42px; font-weight: 700; margin: 8px 0 4px; }}
  .card.total  .value {{ color: #63b3ed; }}
  .card.passed .value {{ color: #48bb78; }}
  .card.failed .value {{ color: #fc8181; }}
  .card.time   .value {{ color: #ed8936; }}
  .card .sub {{ font-size: 12px; color: #718096; }}

  .section {{ background: #1a1f2e; border-radius: 12px; border: 1px solid #2d3748; margin-bottom: 24px; overflow: hidden; }}
  .section-header {{ padding: 20px 24px; border-bottom: 1px solid #2d3748; font-weight: 600; font-size: 15px; display: flex; align-items: center; gap: 10px; }}

  .progress-wrap {{ padding: 20px 24px; }}
  .progress-label {{ display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 13px; color: #718096; }}
  .progress-bar {{ height: 28px; background: #2d3748; border-radius: 6px; overflow: hidden; display: flex; }}
  .bar-seg {{ height: 100%; transition: width 0.3s; }}
  .bar-pass {{ background: #48bb78; }}
  .bar-fail {{ background: #fc8181; }}
  .progress-legend {{ display: flex; gap: 20px; margin-top: 12px; font-size: 13px; }}
  .dot {{ width: 10px; height: 10px; border-radius: 50%; display: inline-block; margin-right: 6px; }}
  .dot-pass {{ background: #48bb78; }}
  .dot-fail {{ background: #fc8181; }}

  .donut-wrap {{ padding: 24px; display: flex; align-items: center; gap: 32px; }}
  .donut {{ position: relative; width: 140px; height: 140px; }}
  .donut svg {{ transform: rotate(-90deg); }}
  .donut-center {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%); text-align: center; }}
  .donut-center .pct {{ font-size: 28px; font-weight: 700; color: #48bb78; }}
  .donut-center .lbl {{ font-size: 11px; color: #718096; }}
  .donut-stats {{ flex: 1; }}
  .donut-stats .stat {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #2d3748; font-size: 14px; }}
  .donut-stats .stat:last-child {{ border: none; }}
  .donut-stats .stat .sval {{ font-weight: 600; }}

  table {{ width: 100%; border-collapse: collapse; }}
  th {{ padding: 12px 16px; text-align: left; font-size: 12px; text-transform: uppercase; letter-spacing: 0.8px; color: #718096; border-bottom: 1px solid #2d3748; }}
  td {{ padding: 14px 16px; font-size: 14px; border-bottom: 1px solid #1e2535; }}
  tr:last-child td {{ border-bottom: none; }}
  tr.pass-row:hover {{ background: #1e2535; }}
  tr.fail-row {{ background: #1f1520; }}
  tr.fail-row:hover {{ background: #251828; }}
  .err-row td {{ padding: 0 16px 12px 48px; }}
  .err-row pre {{ background: #2d1b1b; color: #fc8181; padding: 10px; border-radius: 6px; font-size: 12px; overflow-x: auto; white-space: pre-wrap; }}
  .num {{ color: #718096; width: 40px; }}
  .test-name {{ font-weight: 500; }}
  .test-class {{ color: #718096; font-size: 13px; }}
  .dur {{ color: #718096; }}
  .badge {{ display: inline-flex; align-items: center; gap: 4px; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; }}
  .badge.pass {{ background: #1a3a2a; color: #48bb78; }}
  .badge.fail {{ background: #3a1a1a; color: #fc8181; }}

  .footer {{ text-align: center; padding: 24px; color: #4a5568; font-size: 12px; }}
</style>
</head>
<body>
<header>
  <div>
    <div class="logo">⚡ Selenium Test Report</div>
    <div class="subtitle">Flask Todo App — Automated Browser Testing</div>
  </div>
  <div class="timestamp">Generated: {now}</div>
</header>

<div class="container">

  <!-- Summary cards -->
  <div class="cards">
    <div class="card total">
      <div class="label">Total Tests</div>
      <div class="value">{total}</div>
      <div class="sub">All test cases</div>
    </div>
    <div class="card passed">
      <div class="label">Passed</div>
      <div class="value">{passed}</div>
      <div class="sub">Tests successful</div>
    </div>
    <div class="card failed">
      <div class="label">Failed</div>
      <div class="value">{failed}</div>
      <div class="sub">Tests failed</div>
    </div>
    <div class="card time">
      <div class="label">Duration</div>
      <div class="value">{duration:.1f}s</div>
      <div class="sub">Total run time</div>
    </div>
  </div>

  <!-- Charts row -->
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:24px;">

    <div class="section">
      <div class="section-header">📊 Test Run Distribution</div>
      <div class="progress-wrap">
        <div class="progress-label">
          <span>{passed} passed</span>
          <span>{pct}% success rate</span>
        </div>
        <div class="progress-bar">{bar_segments}</div>
        <div class="progress-legend">
          <span><span class="dot dot-pass"></span>Passed ({passed})</span>
          <span><span class="dot dot-fail"></span>Failed ({failed})</span>
        </div>
      </div>
    </div>

    <div class="section">
      <div class="section-header">🎯 Pass Rate</div>
      <div class="donut-wrap">
        <div class="donut">
          <svg width="140" height="140" viewBox="0 0 140 140">
            <circle cx="70" cy="70" r="54" fill="none" stroke="#2d3748" stroke-width="16"/>
            <circle cx="70" cy="70" r="54" fill="none" stroke="#48bb78" stroke-width="16"
              stroke-dasharray="{round(pct * 3.393, 1)} 339.3"
              stroke-linecap="round"/>
          </svg>
          <div class="donut-center">
            <div class="pct">{pct}%</div>
            <div class="lbl">pass rate</div>
          </div>
        </div>
        <div class="donut-stats">
          <div class="stat"><span>Total Tests</span><span class="sval" style="color:#63b3ed">{total}</span></div>
          <div class="stat"><span>Passed</span><span class="sval" style="color:#48bb78">{passed}</span></div>
          <div class="stat"><span>Failed</span><span class="sval" style="color:#fc8181">{failed}</span></div>
          <div class="stat"><span>Duration</span><span class="sval" style="color:#ed8936">{duration:.2f}s</span></div>
        </div>
      </div>
    </div>

  </div>

  <!-- Results table -->
  <div class="section">
    <div class="section-header">🧪 Test Results</div>
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>Test Name</th>
          <th>Class</th>
          <th>Duration</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
  </div>

</div>
<div class="footer">Flask Todo App · Selenium Automation · Jenkins CI/CD Pipeline</div>
</body>
</html>"""
    return html


def main():
    results = load_results()
    if not results:
        print("No test_results.json found. Run pytest with conftest.py first.")
        sys.exit(1)

    html = build_html(results)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Report generated: {REPORT_FILE}")
    os.startfile(REPORT_FILE)


if __name__ == "__main__":
    main()
