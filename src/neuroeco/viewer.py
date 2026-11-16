"""Visor en tiempo real con pygame (solo visualiza; no modifica la simulación)."""
import numpy as np
import pygame

from .world import World

HUD = 48
BG = (24, 28, 34)
PLANT = (80, 190, 100)
PREY = (90, 160, 255)
PRED = (240, 90, 90)
TEXT = (230, 230, 230)


def _draw_agent(screen, pos, heading, color, radius, alive):
    if not alive:
        return
    x, y = int(pos[0]), int(pos[1]) + HUD
    pygame.draw.circle(screen, color, (x, y), radius)
    tip = (x + int(np.cos(heading) * radius * 1.8), y + int(np.sin(heading) * radius * 1.8))
    pygame.draw.line(screen, (255, 255, 255), (x, y), tip, 2)


def run_viewer(cfg, prey_controller, predator_controller, seed, fps=60,
               max_frames=None, screenshot=None, title="NeuroEcosistema"):
    """Muestra un episodio.

    Teclas: ESPACIO pausa, flechas arriba/abajo velocidad, N nueva semilla,
    R reiniciar la misma semilla, ESC salir.
    """
    pygame.init()
    world = World(cfg, seed)
    ctrl_rng = np.random.default_rng([int(seed), 1])
    screen = pygame.display.set_mode((int(world.W), int(world.H) + HUD))
    pygame.display.set_caption(title)
    font = pygame.font.SysFont("consolas", 14)
    clock = pygame.time.Clock()

    paused, running, frames = False, True, 0
    steps_per_frame = 1
    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False
                elif ev.key == pygame.K_SPACE:
                    paused = not paused
                elif ev.key == pygame.K_UP:
                    steps_per_frame = min(steps_per_frame * 2, 64)
                elif ev.key == pygame.K_DOWN:
                    steps_per_frame = max(steps_per_frame // 2, 1)
                elif ev.key in (pygame.K_n, pygame.K_r):
                    if ev.key == pygame.K_n:
                        seed += 1
                    world = World(cfg, seed)
                    ctrl_rng = np.random.default_rng([int(seed), 1])

        if not paused:
            for _ in range(steps_per_frame):
                if world.done:
                    break
                po = prey_controller.act(world.observe_prey(), ctrl_rng)
                qo = predator_controller.act(world.observe_predator(), ctrl_rng)
                world.step(po, qo)

        screen.fill(BG)
        for i in np.flatnonzero(world.plant_active):
            pygame.draw.circle(screen, PLANT, (int(world.plant_pos[i, 0]), int(world.plant_pos[i, 1]) + HUD), 4)
        for i in range(len(world.prey_pos)):
            _draw_agent(screen, world.prey_pos[i], world.prey_heading[i], PREY, 5, world.prey_alive[i])
        for i in range(len(world.pred_pos)):
            _draw_agent(screen, world.pred_pos[i], world.pred_heading[i], PRED, 8, world.pred_alive[i])

        pygame.draw.rect(screen, (40, 46, 56), (0, 0, int(world.W), HUD))
        l1 = (f"semilla {seed}  paso {world.t}/{world.max_steps}  presas {int(world.prey_alive.sum())}"
              f"  depredadores {int(world.pred_alive.sum())}  plantas {int(world.plant_active.sum())}"
              f"  capturas {int(world.pred_captures.sum())}  x{steps_per_frame}")
        l2 = "[ESPACIO] pausa  [ARRIBA/ABAJO] velocidad  [N] otra semilla  [R] reiniciar  [ESC] salir"
        screen.blit(font.render(l1, True, TEXT), (8, 6))
        screen.blit(font.render(l2, True, TEXT), (8, 26))
        pygame.display.flip()
        clock.tick(fps)

        frames += 1
        if max_frames is not None and frames >= max_frames:
            break

    if screenshot:
        pygame.image.save(screen, screenshot)
    pygame.quit()
    return world