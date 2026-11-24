"""Kiber-Şəbəkə Qoruyucusu üçün Firewall gəmiləri və hərəkət fizikası modulu."""
import pygame
from pygame.sprite import Sprite
from settings import get_folder_images, load_clean_sprite
SHIP_CATALOG = [
    {
        "id": 0,
        "title": "Firewall Alfa",
        "subtitle": "İlkin qoruyucu | Kiber-İmpuls",
        "price": 0,
        "bonus_lives": 0,
        "weapon": "standard",
    },
    {
        "id": 1,
        "title": "Cobalt İnterseptor",
        "subtitle": "+4 Can | Yüksək gərginlik lazeri",
        "price": 150,
        "bonus_lives": 4,
        "weapon": "cobalt",
    },
    {
        "id": 2,
        "title": "Plazma Raketçi",
        "subtitle": "Antivirus ağır raket atışı",
        "price": 250,
        "bonus_lives": 0,
        "weapon": "rocket",
    },
]


class Ship(Sprite):
    """Oyunçunun idarə etdiyi Kiber-Müdafiə gəmisi sinfi."""

    def __init__(self, ai_settings, screen, ship_index: int = 0) -> None:
        """Gəmi şəkillərini yükləyir və ilkin koordinatı təyin edir."""
        super().__init__()
        self.screen = screen
        self.ai_settings = ai_settings
        self.screen_rect = screen.get_rect()

        self.ship_files = get_folder_images("ship")
        self.previews: dict[int, pygame.Surface] = {}
        self.vertical_surfaces: dict[int, pygame.Surface] = {}
        self.sideways_surfaces: dict[int, pygame.Surface] = {}

        for idx in range(3):
            base_surf = self._create_surface(idx, (68, 64))
            self.vertical_surfaces[idx] = base_surf
            self.sideways_surfaces[idx] = pygame.transform.rotate(base_surf, -90)
            self.previews[idx] = self._create_surface(idx, (62, 62))

        self.ship_index = 0
        self.sideways_mode = False
        self.specs = SHIP_CATALOG[0]
        self.image = self.vertical_surfaces[0]
        self.rect = self.image.get_rect()

        self.center = float(self.screen_rect.centerx)
        self.centery = float(self.screen_rect.centery)

        self.moving_right = False
        self.moving_left = False
        self.moving_up = False
        self.moving_down = False
        self.turbo = False

        self.set_ship_index(ship_index)
        self.reset_position(sideways=False)

    def set_ship_index(self, index: int) -> None:
        """Aktiv gəmi modelini (0, 1 və ya 2) seçir."""
        if 0 <= index < len(SHIP_CATALOG):
            self.ship_index = index
            self.specs = SHIP_CATALOG[index]
            self._refresh_orientation_surface()

    def _refresh_orientation_surface(self) -> None:
        """Şaquli və ya Sideways (üfüqi) rejimə uyğun şəkli yeniləyir."""
        if self.sideways_mode:
            self.image = self.sideways_surfaces[self.ship_index]
        else:
            self.image = self.vertical_surfaces[self.ship_index]
        self.rect = self.image.get_rect()

    def reset_position(self, sideways: bool = False) -> None:
        """Seçilmiş oyun rejiminə görə gəmini başlanğıc mövqeyinə qoyur."""
        self.sideways_mode = sideways
        self._refresh_orientation_surface()
        if sideways:
            # Bonus 1: Sideways Shooter — gəmi ekranın sol kənarında yerləşir
            self.rect.left = 18
            self.rect.centery = self.screen_rect.centery
            self.center = float(self.rect.centerx)
            self.centery = float(self.rect.centery)
        else:
            # Klassik rejim — gəmi ekranın alt mərkəzində yerləşir
            self.rect.centerx = self.screen_rect.centerx
            self.rect.bottom = self.screen_rect.bottom - 14
            self.center = float(self.rect.centerx)
            self.centery = float(self.rect.centery)

    def _create_surface(
        self, index: int, size: tuple[int, int]
    ) -> pygame.Surface:
        """assets/ship/ qovluğundan uyğun şəkli yükləyir və ya kiber gəmi çəkir."""
        if index < len(self.ship_files):
            return load_clean_sprite(self.ship_files[index], size)

        w, h = size
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        palettes = [
            ((210, 245, 255), (0, 225, 190), (0, 175, 255)),
            ((70, 130, 240), (140, 205, 255), (40, 110, 255)),
            ((225, 75, 65), (255, 200, 60), (255, 110, 30)),
        ]
        body, wing, glow = palettes[index % 3]
        cx = w // 2
        pygame.draw.polygon(
            surf, wing, [(4, h - 12), (cx - 10, 22), (cx - 10, h - 10)]
        )
        pygame.draw.polygon(
            surf, wing, [(w - 4, h - 12), (cx + 10, 22), (cx + 10, h - 10)]
        )
        pygame.draw.polygon(
            surf,
            body,
            [(cx, 3), (cx - 15, h - 10), (cx, h - 16), (cx + 15, h - 10)],
        )
        pygame.draw.ellipse(surf, glow, (cx - 5, 17, 10, 15))
        return surf

    def get_mini_wingman_surface(self) -> pygame.Surface:
        """3-cü gəmi üçün mini köməkçi dron şəkli qaytarır."""
        base = pygame.transform.smoothscale(self.vertical_surfaces[2], (34, 32))
        return pygame.transform.rotate(base, -90) if self.sideways_mode else base

    def update(self) -> None:
        """Kəsr dəqiqliklə (self.center / self.centery) gəmini hərəkət etdirir."""
        speed = self.ai_settings.ship_speed_factor
        if self.turbo:
            speed *= self.ai_settings.turbo_multiplier

        if self.sideways_mode:
            if self.moving_up and self.rect.top > 56:
                self.centery -= speed
            if self.moving_down and self.rect.bottom < self.screen_rect.bottom - 8:
                self.centery += speed
            self.rect.centery = int(self.centery)
        else:
            if self.moving_right and self.rect.right < self.screen_rect.right:
                self.center += speed
            if self.moving_left and self.rect.left > 0:
                self.center -= speed
            self.rect.centerx = int(self.center)

    def blitme(self, mini_ships: int = 0) -> None:
        """Əsas gəmini və alınmış mini dronları ekrana çəkir."""
        self.screen.blit(self.image, self.rect)

        if self.ship_index == 2 and mini_ships >= 1:
            mini_surf = self.get_mini_wingman_surface()
            if self.sideways_mode:
                r1 = mini_surf.get_rect(
                    centerx=self.rect.centerx + 4,
                    centery=min(self.screen_rect.bottom - 18, self.rect.bottom + 22),
                )
                self.screen.blit(mini_surf, r1)
                if mini_ships >= 2:
                    r2 = mini_surf.get_rect(
                        centerx=self.rect.centerx + 4,
                        centery=max(64, self.rect.top - 22),
                    )
                    self.screen.blit(mini_surf, r2)
            else:
                r1 = mini_surf.get_rect(
                    centerx=min(self.screen_rect.right - 18, self.rect.right + 24),
                    centery=self.rect.centery + 6,
                )
                self.screen.blit(mini_surf, r1)
                if mini_ships >= 2:
                    r2 = mini_surf.get_rect(
                        centerx=max(18, self.rect.left - 24),
                        centery=self.rect.centery + 6,
                    )
                    self.screen.blit(mini_surf, r2)
