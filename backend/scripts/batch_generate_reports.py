#!/usr/bin/env python3
"""
批量生成Deep Research报告测试脚本

用法:
    python scripts/batch_generate_reports.py --signal-ids 1,16,17,20,23,...
    python scripts/batch_generate_reports.py --from-file reports/test_signals.json
"""

import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models.signal import Signal
from app.services.deep_research_service import DeepResearchService, ResearchStrategy


class BatchReportGenerator:
    def __init__(self):
        self.service = DeepResearchService()
        self.db = SessionLocal()
        self.results: List[Dict[str, Any]] = []

    async def generate_one(self, signal_id: int, force: bool = True) -> Dict[str, Any]:
        """生成单个报告"""
        print(f"\n{'='*60}")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 开始处理 Signal #{signal_id}")

        result = {
            "signal_id": signal_id,
            "start_time": time.time(),
            "status": "pending",
            "error": None,
            "cost": 0,
            "tokens": 0,
            "duration": 0
        }

        try:
            # 获取信号
            signal = self.db.query(Signal).filter(Signal.id == signal_id).first()
            if not signal:
                raise ValueError(f"Signal #{signal_id} 不存在")

            print(f"  标题: {signal.title[:60]}...")
            print(f"  来源: {signal.source} | 评分: {signal.final_score}★")

            # 生成报告
            print(f"  正在生成报告...")
            start = time.time()

            research_result = await self.service.generate_research(
                signal=signal,
                strategy=ResearchStrategy.LIGHTWEIGHT,
                force_regenerate=force
            )

            duration = time.time() - start

            # 更新结果
            result.update({
                "status": "success",
                "cost": research_result.cost_usd,
                "tokens": research_result.tokens_used,
                "duration": duration,
                "report_length": len(research_result.content),
                "sources_count": len(research_result.sources)
            })

            print(f"  ✅ 成功!")
            print(f"     时长: {duration:.1f}秒")
            print(f"     成本: ${research_result.cost_usd:.4f}")
            print(f"     Token: {research_result.tokens_used}")
            print(f"     报告长度: {len(research_result.content)} 字符")

        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            print(f"  ❌ 失败: {e}")

        finally:
            result["end_time"] = time.time()
            result["duration"] = result["end_time"] - result["start_time"]

        return result

    async def generate_batch(self, signal_ids: List[int], force: bool = True, delay: int = 3):
        """批量生成"""
        print(f"\n🚀 开始批量生成 Deep Research 报告")
        print(f"   总数: {len(signal_ids)} 个信号")
        print(f"   策略: Lightweight V1")
        print(f"   强制重新生成: {'是' if force else '否'}")
        print(f"   间隔延迟: {delay} 秒")

        for i, signal_id in enumerate(signal_ids, 1):
            print(f"\n进度: {i}/{len(signal_ids)}")

            result = await self.generate_one(signal_id, force)
            self.results.append(result)

            # 延迟避免API限流
            if i < len(signal_ids):
                print(f"\n⏳ 等待 {delay} 秒...")
                await asyncio.sleep(delay)

        self._print_summary()
        self._save_results()

    def _print_summary(self):
        """打印汇总统计"""
        print(f"\n{'='*60}")
        print(f"📊 批量生成完成 - 汇总统计")
        print(f"{'='*60}")

        total = len(self.results)
        success = len([r for r in self.results if r['status'] == 'success'])
        failed = total - success

        print(f"\n总数: {total}")
        print(f"  ✅ 成功: {success} ({success/total*100:.1f}%)")
        print(f"  ❌ 失败: {failed} ({failed/total*100:.1f}%)")

        if success > 0:
            success_results = [r for r in self.results if r['status'] == 'success']

            total_cost = sum(r['cost'] for r in success_results)
            total_tokens = sum(r['tokens'] for r in success_results)
            avg_duration = sum(r['duration'] for r in success_results) / success
            avg_cost = total_cost / success
            avg_tokens = total_tokens / success

            print(f"\n成本统计:")
            print(f"  总成本: ${total_cost:.4f}")
            print(f"  平均成本: ${avg_cost:.4f}")
            print(f"  成本范围: ${min(r['cost'] for r in success_results):.4f} - ${max(r['cost'] for r in success_results):.4f}")

            print(f"\nToken统计:")
            print(f"  总Token: {total_tokens}")
            print(f"  平均Token: {avg_tokens:.0f}")

            print(f"\n时间统计:")
            print(f"  平均时长: {avg_duration:.1f} 秒")
            print(f"  最快: {min(r['duration'] for r in success_results):.1f} 秒")
            print(f"  最慢: {max(r['duration'] for r in success_results):.1f} 秒")

        if failed > 0:
            print(f"\n失败详情:")
            for r in [r for r in self.results if r['status'] == 'failed']:
                print(f"  Signal #{r['signal_id']}: {r['error']}")

    def _save_results(self):
        """保存结果到文件"""
        output_file = Path(__file__).parent.parent / "reports" / f"batch_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_file.parent.mkdir(exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "total": len(self.results),
                    "success": len([r for r in self.results if r['status'] == 'success']),
                    "failed": len([r for r in self.results if r['status'] == 'failed'])
                },
                "results": self.results
            }, f, indent=2, ensure_ascii=False)

        print(f"\n💾 结果已保存到: {output_file}")


async def main():
    import argparse

    parser = argparse.ArgumentParser(description='批量生成Deep Research报告')
    parser.add_argument('--signal-ids', type=str, help='信号ID列表,逗号分隔 (如: 1,16,17,20)')
    parser.add_argument('--from-file', type=str, help='从JSON文件读取信号ID列表')
    parser.add_argument('--force', action='store_true', default=True, help='强制重新生成 (默认: True)')
    parser.add_argument('--delay', type=int, default=3, help='每次生成间隔秒数 (默认: 3)')

    args = parser.parse_args()

    # 获取信号ID列表
    signal_ids = []

    if args.from_file:
        with open(args.from_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            signal_ids = [s['id'] for s in data['test_signals']]
    elif args.signal_ids:
        signal_ids = [int(x.strip()) for x in args.signal_ids.split(',')]
    else:
        print("❌ 错误: 请提供 --signal-ids 或 --from-file 参数")
        return

    if not signal_ids:
        print("❌ 错误: 信号ID列表为空")
        return

    # 执行批量生成
    generator = BatchReportGenerator()
    await generator.generate_batch(signal_ids, force=args.force, delay=args.delay)


if __name__ == "__main__":
    asyncio.run(main())
