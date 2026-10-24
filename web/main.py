"""Entrée navigateur : mêmes règles et rendu, boucle coopérative uniquement."""
import asyncio
import time

import pygame
import platform

from luna.ui.app import GameApp


app = None


def browser_size():
    return int(platform.window.lunaWidth), int(platform.window.lunaHeight)


async def main():
    global app
    app = GameApp(size=browser_size())
    pygame.event.clear()  # Le clic Jouer ne sélectionne pas une fleur.
    previous = time.perf_counter()
    hidden = False
    while True:
        if platform.document.hidden:
            if not hidden:
                app.audio.stop()
                hidden = True
            await asyncio.sleep(.1)
            continue
        hidden = False
        now = time.perf_counter()
        dt, previous = now - previous, now
        size = browser_size()
        if app.screen.get_size() != size:
            app.screen = pygame.display.set_mode(size)
        for event in pygame.event.get():
            app.handle_event(event)
        if not app.running:
            app.audio.stop()
            app.skip_presentation()
            platform.window.lunaPause()
            while not platform.window.lunaStarted:
                await asyncio.sleep(.05)
            pygame.event.clear()
            app.running = True
            previous = time.perf_counter()
            dt = 0
        app.update(dt)
        app.draw()
        await asyncio.sleep(0)


asyncio.run(main())
