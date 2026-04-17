"""Playwright 截图工具，用于渲染 Mermaid 图表并输出 PNG/SVG。"""

import argparse
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout


def capture_diagram(
    html_url: str,
    output_png: str,
    output_svg: str = None,
    timeout: int = 30000,
) -> dict:
    """使用 Playwright 截图图表。

    Args:
        html_url: 本地 HTTP 服务的 HTML 页面 URL
        output_png: 输出的 PNG 文件路径
        output_svg: 可选，输出的 SVG 文件路径
        timeout: 等待渲染超时时间（毫秒）

    Returns:
        dict 包含结果信息
        - success: bool
        - error: str 或 None
        - render_failed: bool（Mermaid 渲染失败标志）
    """
    result = {
        "success": False,
        "error": None,
        "render_failed": False,
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1200, "height": 800})

        try:
            # 访问页面
            page.goto(html_url, wait_until="networkidle", timeout=timeout)

            # 等待 Mermaid 渲染完成
            page.wait_for_selector(".mermaid svg", timeout=10000)

            # 检查是否有渲染错误
            error_icon = page.query_selector(".mermaid .error-icon")
            if error_icon:
                result["render_failed"] = True
                result["error"] = "Mermaid rendering failed (syntax error)"
                browser.close()
                return result

            # 等待一下确保渲染稳定
            time.sleep(0.5)

            # 获取 SVG 元素并截图
            svg_element = page.query_selector(".mermaid svg")
            if not svg_element:
                result["error"] = "SVG element not found after rendering"
                browser.close()
                return result

            # PNG 截图
            svg_element.screenshot(path=output_png)
            result["success"] = True

            # SVG 提取（如果请求）
            if output_svg:
                svg_content = svg_element.evaluate("el => el.outerHTML")
                Path(output_svg).write_text(svg_content, encoding="utf-8")

        except PlaywrightTimeout:
            result["error"] = f"Timeout waiting for rendering ({timeout}ms)"
        except Exception as e:
            result["error"] = str(e)
        finally:
            browser.close()

    return result


def main():
    """CLI 入口。"""
    parser = argparse.ArgumentParser(description="Capture Mermaid diagram screenshot")
    parser.add_argument("--url", required=True, help="HTML page URL")
    parser.add_argument("--output", required=True, help="Output PNG file path")
    parser.add_argument("--svg", help="Optional output SVG file path")
    parser.add_argument(
        "--timeout", type=int, default=30000, help="Timeout in milliseconds"
    )

    args = parser.parse_args()

    result = capture_diagram(
        html_url=args.url,
        output_png=args.output,
        output_svg=args.svg,
        timeout=args.timeout,
    )

    if result["success"]:
        print(f"SUCCESS: PNG saved to {args.output}")
        if args.svg:
            print(f"SUCCESS: SVG saved to {args.svg}")
        sys.exit(0)
    elif result["render_failed"]:
        print(f"RENDER_FAILED: {result['error']}", file=sys.stderr)
        sys.exit(2)
    else:
        print(f"ERROR: {result['error']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
