from binusWifiAPI import app

if __name__ == "__main__":
    import hypercorn.asyncio
    import hypercorn.config
    import asyncio

    config = hypercorn.config.Config()
    config.bind = ["0.0.0.0:5000"]

    asyncio.run(hypercorn.asyncio.serve(app, config))
