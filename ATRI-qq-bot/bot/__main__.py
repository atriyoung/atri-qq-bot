"""入口模块

用法:
    python -m bot                      # 默认配置
    python -m bot --config config/bot.yaml
"""

import sys
import asyncio

from .utils.logger import setup_logger
from .app import Application


def main():
    setup_logger()

    config_path = "config/bot.yaml"
    if len(sys.argv) > 2 and sys.argv[1] == "--config":
        config_path = sys.argv[2]

    app = Application(config_path)

    async def run():
        await app.initialize()
        await app.start()
        await app.wait_forever()

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
