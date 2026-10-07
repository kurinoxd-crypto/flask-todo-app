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
        return [], 0
    with open(RESULTS_FILE) as f:
        data = json.load(f)
    # Support both new format {total_duration, results} and legacy flat list
    if isinstance(data, dict):
        return data.get("results", []), data.get("total_duration", 0)
    else:
        results = data
        return results, sum(r["duration"] for r in results)


def build_html(results, total_duration):
    total    = len(results)
    passed   = sum(1 for r in results if r["status"] == "PASSED")
    failed   = sum(1 for r in results if r["status"] == "FAILED")
    pct      = round((passed / total * 100) if total else 0, 1)
    now      = datetime.now().strftime("%d %b %Y  %H:%M:%S")

    rows = ""
    for i, r in enumerate(results):
        status_class = "pass" if r["status"] == "PASSED" else "fail"
        status_icon  = "✓" if r["status"] == "PASSED" else "✗"
        err_row = ""
        if r.get("error"):
            err_row = f'''
        <tr class="error-row">
            <td colspan="5">
                <div class="error-content">{r["error"]}</div>
            </td>
        </tr>'''
        rows += f'''
        <tr class="{status_class}-row">
            <td class="test-num">{i+1}</td>
            <td class="test-name">{r['name']}</td>
            <td class="test-class">{r['class']}</td>
            <td class="test-duration">{r['duration']:.2f}s</td>
            <td>
                <span class="status-badge {status_class}">
                    <span class="status-icon">{status_icon}</span>
                    {r['status']}
                </span>
            </td>
        </tr>{err_row}'''

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
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
<title>Test Results — Selenium Report</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ 
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', sans-serif;
    background: #f5f7fa;
    color: #2d3748;
    min-height: 100vh;
    line-height: 1.5;
  }}

  /* Header */
  header {{
    background: #fff;
    border-bottom: 1px solid #e2e8f0;
    padding: 20px 32px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  }}
  .header-content {{ max-width: 1400px; margin: 0 auto; display: flex; align-items: center; justify-content: space-between; }}
  .logo {{ display: flex; align-items: center; gap: 12px; }}
  .logo-icon {{ 
    width: 36px; height: 36px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 8px; display: flex; align-items: center; justify-content: center;
    color: white; font-size: 20px; font-weight: bold;
  }}
  .logo-text {{ font-size: 20px; font-weight: 600; color: #1a202c; }}
  .timestamp {{ color: #718096; font-size: 14px; }}

  /* Container */
  .container {{ max-width: 1400px; margin: 0 auto; padding: 32px; }}

  /* Overview Section */
  .overview {{ background: white; border-radius: 12px; padding: 32px; margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
  .overview-header {{ display: flex; align-items: center; gap: 12px; margin-bottom: 24px; }}
  .overview-header h2 {{ font-size: 18px; font-weight: 600; color: #1a202c; }}

  /* Stats Grid */
  .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 24px; }}
  .stat-card {{
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 20px;
    background: #f7fafc;
    border-radius: 10px;
    border: 1px solid #e2e8f0;
    transition: all 0.2s;
  }}
  .stat-card:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.08); }}
  
  .stat-icon {{
    width: 48px; height: 48px;
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px;
    flex-shrink: 0;
  }}
  .stat-icon.total {{ background: #ebf4ff; color: #3182ce; }}
  .stat-icon.passed {{ background: #e6fffa; color: #38a169; }}
  .stat-icon.failed {{ background: #fff5f5; color: #e53e3e; }}
  .stat-icon.time {{ background: #fef5e7; color: #dd6b20; }}

  .stat-info {{ flex: 1; }}
  .stat-label {{ font-size: 13px; color: #718096; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; }}
  .stat-value {{ font-size: 28px; font-weight: 700; color: #1a202c; margin-top: 2px; }}
  .stat-desc {{ font-size: 12px; color: #a0aec0; margin-top: 2px; }}

  /* Charts Section */
  .charts-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 24px; }}
  
  @media (max-width: 968px) {{
    .charts-row {{ grid-template-columns: 1fr; }}
  }}

  .chart-card {{
    background: white;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  }}
  .chart-header {{ 
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 20px;
    padding-bottom: 16px;
    border-bottom: 1px solid #e2e8f0;
  }}
  .chart-header h3 {{ font-size: 16px; font-weight: 600; color: #1a202c; }}

  /* Progress Bar */
  .progress-info {{ display: flex; justify-content: space-between; margin-bottom: 12px; font-size: 13px; }}
  .progress-info-left {{ color: #2d3748; font-weight: 500; }}
  .progress-info-right {{ color: #718096; }}
  
  .progress-bar-container {{ 
    height: 32px;
    background: #edf2f7;
    border-radius: 8px;
    overflow: hidden;
    display: flex;
    margin-bottom: 16px;
  }}
  .bar-seg {{ height: 100%; transition: all 0.4s ease; }}
  .bar-pass {{ background: linear-gradient(90deg, #48bb78 0%, #38a169 100%); }}
  .bar-fail {{ background: linear-gradient(90deg, #fc8181 0%, #f56565 100%); }}
  
  .progress-legend {{ display: flex; gap: 24px; font-size: 14px; }}
  .legend-item {{ display: flex; align-items: center; gap: 8px; }}
  .legend-dot {{ width: 12px; height: 12px; border-radius: 3px; }}
  .legend-dot.pass {{ background: #48bb78; }}
  .legend-dot.fail {{ background: #fc8181; }}
  .legend-label {{ color: #4a5568; font-weight: 500; }}
  .legend-count {{ color: #718096; }}

  /* Donut Chart */
  .donut-container {{ display: flex; align-items: center; gap: 40px; }}
  .donut-chart {{ position: relative; width: 150px; height: 150px; flex-shrink: 0; }}
  .donut-chart svg {{ transform: rotate(-90deg); filter: drop-shadow(0 2px 8px rgba(0,0,0,0.1)); }}
  .donut-center {{ 
    position: absolute;
    top: 50%; left: 50%;
    transform: translate(-50%,-50%);
    text-align: center;
  }}
  .donut-pct {{ font-size: 32px; font-weight: 700; color: #38a169; line-height: 1; }}
  .donut-label {{ font-size: 12px; color: #a0aec0; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.5px; }}

  .donut-stats {{ flex: 1; display: flex; flex-direction: column; gap: 12px; }}
  .donut-stat {{ 
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px;
    background: #f7fafc;
    border-radius: 8px;
  }}
  .donut-stat-label {{ color: #4a5568; font-size: 14px; font-weight: 500; }}
  .donut-stat-value {{ font-weight: 700; font-size: 16px; }}

  /* Results Table */
  .results-card {{
    background: white;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  }}
  .results-header {{
    padding: 24px;
    border-bottom: 1px solid #e2e8f0;
    display: flex;
    align-items: center;
    gap: 10px;
  }}
  .results-header h3 {{ font-size: 16px; font-weight: 600; color: #1a202c; }}

  table {{ width: 100%; border-collapse: collapse; }}
  thead {{ background: #f7fafc; }}
  th {{ 
    padding: 14px 20px;
    text-align: left;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #4a5568;
    border-bottom: 2px solid #e2e8f0;
  }}
  tbody tr {{ transition: background 0.15s; }}
  tbody tr:hover {{ background: #f7fafc; }}
  tbody tr.fail-row {{ background: #fffaf0; }}
  tbody tr.fail-row:hover {{ background: #fef5e7; }}
  
  td {{ 
    padding: 16px 20px;
    font-size: 14px;
    border-bottom: 1px solid #edf2f7;
  }}
  tbody tr:last-child td {{ border-bottom: none; }}

  .test-num {{ color: #a0aec0; font-weight: 500; width: 60px; }}
  .test-name {{ color: #1a202c; font-weight: 500; }}
  .test-class {{ color: #718096; font-size: 13px; }}
  .test-duration {{ color: #718096; font-variant-numeric: tabular-nums; }}
  
  .status-badge {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 600;
  }}
  .status-badge.pass {{ background: #e6fffa; color: #2f855a; }}
  .status-badge.fail {{ background: #fff5f5; color: #c53030; }}
  .status-icon {{ font-size: 14px; }}

  .error-row {{ background: #fffaf0; }}
  .error-row td {{ padding: 0 20px 16px 80px; border: none; }}
  .error-content {{ 
    background: #fef5e7;
    border-left: 3px solid #e53e3e;
    padding: 12px 16px;
    border-radius: 6px;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 12px;
    color: #c53030;
    overflow-x: auto;
    white-space: pre-wrap;
  }}

  /* Footer */
  .footer {{
    text-align: center;
    padding: 32px;
    color: #a0aec0;
    font-size: 13px;
  }}
  .footer-links {{ display: flex; justify-content: center; gap: 16px; margin-top: 8px; }}
  .footer-link {{ color: #718096; text-decoration: none; }}
  .footer-link:hover {{ color: #4a5568; }}
</style>
</head>
<body>
<header>
  <div class="header-content">
    <div class="logo">
      <div class="logo-icon">T</div>
      <div>
        <div class="logo-text">Test Results</div>
      </div>
    </div>
    <div class="timestamp">Generated {now}</div>
  </div>
</header>

<div class="container">

  <!-- Overview Section -->
  <div class="overview">
    <div class="overview-header">
      <span style="font-size:20px;">📊</span>
      <h2>Test Run Overview</h2>
    </div>
    
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon total">📝</div>
        <div class="stat-info">
          <div class="stat-label">Total Tests</div>
          <div class="stat-value">{total}</div>
          <div class="stat-desc">Test cases executed</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon passed">✓</div>
        <div class="stat-info">
          <div class="stat-label">Passed</div>
          <div class="stat-value">{passed}</div>
          <div class="stat-desc">Successful tests</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon failed">✗</div>
        <div class="stat-info">
          <div class="stat-label">Failed</div>
          <div class="stat-value">{failed}</div>
          <div class="stat-desc">Failed tests</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon time">⏱</div>
        <div class="stat-info">
          <div class="stat-label">Duration</div>
          <div class="stat-value">{total_duration:.1f}s</div>
          <div class="stat-desc">Total execution time</div>
        </div>
      </div>
    </div>
  </div>

  <!-- Charts Row -->
  <div class="charts-row">
    
    <!-- Distribution Chart -->
    <div class="chart-card">
      <div class="chart-header">
        <span style="font-size:18px;">📈</span>
        <h3>Test Distribution</h3>
      </div>
      <div>
        <div class="progress-info">
          <span class="progress-info-left">{passed} of {total} tests passed</span>
          <span class="progress-info-right">{pct}% success rate</span>
        </div>
        <div class="progress-bar-container">{bar_segments}</div>
        <div class="progress-legend">
          <div class="legend-item">
            <div class="legend-dot pass"></div>
            <span class="legend-label">Passed</span>
            <span class="legend-count">({passed})</span>
          </div>
          <div class="legend-item">
            <div class="legend-dot fail"></div>
            <span class="legend-label">Failed</span>
            <span class="legend-count">({failed})</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Pass Rate Chart -->
    <div class="chart-card">
      <div class="chart-header">
        <span style="font-size:18px;">🎯</span>
        <h3>Pass Rate</h3>
      </div>
      <div class="donut-container">
        <div class="donut-chart">
          <svg width="150" height="150" viewBox="0 0 150 150">
            <circle cx="75" cy="75" r="60" fill="none" stroke="#e2e8f0" stroke-width="20"/>
            <circle cx="75" cy="75" r="60" fill="none" stroke="#38a169" stroke-width="20"
              stroke-dasharray="{round(pct * 3.77, 1)} 377"
              stroke-linecap="round"/>
          </svg>
          <div class="donut-center">
            <div class="donut-pct">{pct}%</div>
            <div class="donut-label">Success</div>
          </div>
        </div>
        <div class="donut-stats">
          <div class="donut-stat">
            <span class="donut-stat-label">Total Tests</span>
            <span class="donut-stat-value" style="color:#3182ce">{total}</span>
          </div>
          <div class="donut-stat">
            <span class="donut-stat-label">Passed</span>
            <span class="donut-stat-value" style="color:#38a169">{passed}</span>
          </div>
          <div class="donut-stat">
            <span class="donut-stat-label">Failed</span>
            <span class="donut-stat-value" style="color:#e53e3e">{failed}</span>
          </div>
          <div class="donut-stat">
            <span class="donut-stat-label">Duration</span>
            <span class="donut-stat-value" style="color:#dd6b20">{total_duration:.2f}s</span>
          </div>
        </div>
      </div>
    </div>

  </div>

  <!-- Results Table -->
  <div class="results-card">
    <div class="results-header">
      <span style="font-size:18px;">🧪</span>
      <h3>Detailed Test Results</h3>
    </div>
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

<div class="footer">
  <div>Flask Todo App · Selenium Automated Testing</div>
  <div class="footer-links">
    <a href="#" class="footer-link">Jenkins CI/CD</a>
    <span style="color:#cbd5e0">·</span>
    <a href="#" class="footer-link">Selenium WebDriver</a>
    <span style="color:#cbd5e0">·</span>
    <a href="#" class="footer-link">Python Pytest</a>
  </div>
</div>
</body>
</html>"""
    return html


def main():
    results, total_duration = load_results()
    if not results:
        print("No test_results.json found. Run pytest with conftest.py first.")
        sys.exit(1)

    html = build_html(results, total_duration)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Report generated: {REPORT_FILE}")


if __name__ == "__main__":
    main()
