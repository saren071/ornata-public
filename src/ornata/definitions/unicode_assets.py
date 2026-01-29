"""
UI Unicode Assets
=================
Centralized repository for UI rendering characters.
"""

# =============================================================================
# 1. BOX DRAWING CONSTANTS
# =============================================================================

# Light
BOX_LIGHT_HORIZONTAL = '─'
BOX_LIGHT_VERTICAL = '│'
BOX_LIGHT_DOWN_RIGHT = '┌'
BOX_LIGHT_DOWN_LEFT = '┐'
BOX_LIGHT_UP_RIGHT = '└'
BOX_LIGHT_UP_LEFT = '┘'
BOX_LIGHT_VERTICAL_RIGHT = '├'
BOX_LIGHT_VERTICAL_LEFT = '┤'
BOX_LIGHT_DOWN_HORIZONTAL = '┬'
BOX_LIGHT_UP_HORIZONTAL = '┴'
BOX_LIGHT_CROSS = '┼'

# Heavy
BOX_HEAVY_HORIZONTAL = '━'
BOX_HEAVY_VERTICAL = '┃'
BOX_HEAVY_DOWN_RIGHT = '┏'
BOX_HEAVY_DOWN_LEFT = '┓'
BOX_HEAVY_UP_RIGHT = '┗'
BOX_HEAVY_UP_LEFT = '┛'
BOX_HEAVY_VERTICAL_RIGHT = '┣'
BOX_HEAVY_VERTICAL_LEFT = '┫'
BOX_HEAVY_DOWN_HORIZONTAL = '┳'
BOX_HEAVY_UP_HORIZONTAL = '┻'
BOX_HEAVY_CROSS = '╋'

# Double
BOX_DOUBLE_HORIZONTAL = '═'
BOX_DOUBLE_VERTICAL = '║'
BOX_DOUBLE_DOWN_RIGHT = '╔'
BOX_DOUBLE_DOWN_LEFT = '╗'
BOX_DOUBLE_UP_RIGHT = '╚'
BOX_DOUBLE_UP_LEFT = '╝'
BOX_DOUBLE_VERTICAL_RIGHT = '╠'
BOX_DOUBLE_VERTICAL_LEFT = '╣'
BOX_DOUBLE_DOWN_HORIZONTAL = '╦'
BOX_DOUBLE_UP_HORIZONTAL = '╩'
BOX_DOUBLE_CROSS = '╬'

# Rounded (Arcs)
BOX_ARC_DOWN_RIGHT = '╭'
BOX_ARC_DOWN_LEFT = '╮'
BOX_ARC_UP_LEFT = '╯'
BOX_ARC_UP_RIGHT = '╰'

# Dashed / Dotted
BOX_LIGHT_TRIPLE_DASH_HZ = '┄'
BOX_HEAVY_TRIPLE_DASH_HZ = '┅'
BOX_LIGHT_TRIPLE_DASH_VT = '┆'
BOX_HEAVY_TRIPLE_DASH_VT = '┇'
BOX_LIGHT_QUAD_DASH_HZ = '┈'
BOX_HEAVY_QUAD_DASH_HZ = '┉'
BOX_LIGHT_QUAD_DASH_VT = '┊'
BOX_HEAVY_QUAD_DASH_VT = '┋'
BOX_LIGHT_DOUBLE_DASH_HZ = '╌'
BOX_HEAVY_DOUBLE_DASH_HZ = '╍'
BOX_LIGHT_DOUBLE_DASH_VT = '╎'
BOX_HEAVY_DOUBLE_DASH_VT = '╏'

# Mixed Weights (Down/Up/Left/Right directions indicate the HEAVY side)
BOX_DOWN_LIGHT_RIGHT_HEAVY = '┍'
BOX_DOWN_HEAVY_RIGHT_LIGHT = '┎'
BOX_DOWN_LIGHT_LEFT_HEAVY = '┑'
BOX_DOWN_HEAVY_LEFT_LIGHT = '┒'
BOX_UP_LIGHT_RIGHT_HEAVY = '┕'
BOX_UP_HEAVY_RIGHT_LIGHT = '┖'
BOX_UP_LIGHT_LEFT_HEAVY = '┙'
BOX_UP_HEAVY_LEFT_LIGHT = '┚'

# Diagonals
BOX_DIAGONAL_UP_RIGHT = '╱'
BOX_DIAGONAL_UP_LEFT = '╲'
BOX_DIAGONAL_CROSS = '╳'

# =============================================================================
# 2. BORDER STYLE COLLECTIONS
# =============================================================================

BORDER_STYLES = {
    'light': {
        'h': BOX_LIGHT_HORIZONTAL,
        'v': BOX_LIGHT_VERTICAL,
        'tl': BOX_LIGHT_DOWN_RIGHT,
        'tr': BOX_LIGHT_DOWN_LEFT,
        'bl': BOX_LIGHT_UP_RIGHT,
        'br': BOX_LIGHT_UP_LEFT,
        'vr': BOX_LIGHT_VERTICAL_RIGHT,
        'vl': BOX_LIGHT_VERTICAL_LEFT,
        'dh': BOX_LIGHT_DOWN_HORIZONTAL,
        'uh': BOX_LIGHT_UP_HORIZONTAL,
        'x': BOX_LIGHT_CROSS,
    },
    'heavy': {
        'h': BOX_HEAVY_HORIZONTAL,
        'v': BOX_HEAVY_VERTICAL,
        'tl': BOX_HEAVY_DOWN_RIGHT,
        'tr': BOX_HEAVY_DOWN_LEFT,
        'bl': BOX_HEAVY_UP_RIGHT,
        'br': BOX_HEAVY_UP_LEFT,
        'vr': BOX_HEAVY_VERTICAL_RIGHT,
        'vl': BOX_HEAVY_VERTICAL_LEFT,
        'dh': BOX_HEAVY_DOWN_HORIZONTAL,
        'uh': BOX_HEAVY_UP_HORIZONTAL,
        'x': BOX_HEAVY_CROSS,
    },
    'double': {
        'h': BOX_DOUBLE_HORIZONTAL,
        'v': BOX_DOUBLE_VERTICAL,
        'tl': BOX_DOUBLE_DOWN_RIGHT,
        'tr': BOX_DOUBLE_DOWN_LEFT,
        'bl': BOX_DOUBLE_UP_RIGHT,
        'br': BOX_DOUBLE_UP_LEFT,
        'vr': BOX_DOUBLE_VERTICAL_RIGHT,
        'vl': BOX_DOUBLE_VERTICAL_LEFT,
        'dh': BOX_DOUBLE_DOWN_HORIZONTAL,
        'uh': BOX_DOUBLE_UP_HORIZONTAL,
        'x': BOX_DOUBLE_CROSS,
    },
    'rounded': {
        'h': BOX_LIGHT_HORIZONTAL,
        'v': BOX_LIGHT_VERTICAL,
        'tl': BOX_ARC_DOWN_RIGHT,
        'tr': BOX_ARC_DOWN_LEFT,
        'bl': BOX_ARC_UP_RIGHT,
        'br': BOX_ARC_UP_LEFT,
        # Rounded usually re-uses light junctions
        'vr': BOX_LIGHT_VERTICAL_RIGHT,
        'vl': BOX_LIGHT_VERTICAL_LEFT,
        'dh': BOX_LIGHT_DOWN_HORIZONTAL,
        'uh': BOX_LIGHT_UP_HORIZONTAL,
        'x': BOX_LIGHT_CROSS,
    },
}

# =============================================================================
# 3. BLOCK ELEMENTS & BARS
# =============================================================================

# Shades
BLOCK_SHADE_LIGHT = '░'
BLOCK_SHADE_MEDIUM = '▒'
BLOCK_SHADE_DARK = '▓'

# Vertical Blocks (Height increases)
BLOCK_LOWER_1_8 = ' '
BLOCK_LOWER_2_8 = '▂'
BLOCK_LOWER_3_8 = '▃'
BLOCK_LOWER_4_8 = '▄'
BLOCK_LOWER_5_8 = '▅'
BLOCK_LOWER_6_8 = '▆'
BLOCK_LOWER_7_8 = '▇'
# BLOCK_FULL serves as 8/8
BLOCK_UPPER_HALF = '▀'

# Horizontal Blocks (Width increases left-to-right)
BLOCK_LEFT_1_8 = '▏'
BLOCK_LEFT_2_8 = '▎'
BLOCK_LEFT_3_8 = '▍'
BLOCK_LEFT_4_8 = '▌'
BLOCK_LEFT_5_8 = '▋'
BLOCK_LEFT_6_8 = '▊'
BLOCK_LEFT_7_8 = '▉'
# BLOCK_FULL serves as 8/8

BLOCK_FULL = '█'

# Quadrants
BLOCK_QUAD_LOWER_LEFT = '▖'
BLOCK_QUAD_LOWER_RIGHT = '▗'
BLOCK_QUAD_UPPER_LEFT = '▘'
BLOCK_QUAD_UPPER_RIGHT = '▝'

# --- Collections for Progress Bars ---

BAR_LEVELS_VERTICAL = [
    ' ',                # 0/8 (Empty)
    BLOCK_LOWER_1_8,    # 1/8
    BLOCK_LOWER_2_8,    # 2/8
    BLOCK_LOWER_3_8,    # 3/8
    BLOCK_LOWER_4_8,    # 4/8 (Half)
    BLOCK_LOWER_5_8,    # 5/8
    BLOCK_LOWER_6_8,    # 6/8
    BLOCK_LOWER_7_8,    # 7/8
    BLOCK_FULL,         # 8/8 (Full)
]

BAR_LEVELS_HORIZONTAL = [
    ' ',                # 0/8 (Empty)
    BLOCK_LEFT_1_8,     # 1/8
    BLOCK_LEFT_2_8,     # 2/8
    BLOCK_LEFT_3_8,     # 3/8
    BLOCK_LEFT_4_8,     # 4/8 (Half)
    BLOCK_LEFT_5_8,     # 5/8
    BLOCK_LEFT_6_8,     # 6/8
    BLOCK_LEFT_7_8,     # 7/8
    BLOCK_FULL,         # 8/8 (Full)
]

SHADES = [
    ' ',
    BLOCK_SHADE_LIGHT,
    BLOCK_SHADE_MEDIUM,
    BLOCK_SHADE_DARK,
    BLOCK_FULL,
]

# =============================================================================
# 4. ICONS & SHAPES
# =============================================================================

# Common UI Icons
ICON_CHECK = '✔'
ICON_CROSS = '✘'
ICON_RADIO_ON = '◉'
ICON_RADIO_OFF = '○'
ICON_CHECKBOX_ON = '☑'
ICON_CHECKBOX_OFF = '☐'
ICON_STAR_FILLED = '★'
ICON_STAR_EMPTY = '☆'
ICON_HEART_FILLED = '♥'
ICON_HEART_EMPTY = '♡'
ICON_WARNING = '⚠'
ICON_ERROR = '⛔'
ICON_INFO = 'ℹ'
ICON_SETTINGS = '⚙'
ICON_LOCK = '🔒'
ICON_UNLOCK = '🔓'
ICON_MAIL = '✉'
ICON_EDIT = '✎'
ICON_DELETE = '✄'
ICON_SEARCH = '⚲'

# Arrows (Directional)
ARROW_LEFT = '←'
ARROW_UP = '↑'
ARROW_RIGHT = '→'
ARROW_DOWN = '↓'
ARROW_LEFT_RIGHT = '↔'
ARROW_UP_DOWN = '↕'

TRIANGLE_UP = '▲'
TRIANGLE_DOWN = '▼'
TRIANGLE_LEFT = '◀'
TRIANGLE_RIGHT = '▶'
TRIANGLE_UP_SMALL = '▴'
TRIANGLE_DOWN_SMALL = '▾'
TRIANGLE_LEFT_SMALL = '◂'
TRIANGLE_RIGHT_SMALL = '▸'

# =============================================================================
# 5. ASSET LISTS (Categorized)
# =============================================================================

# Full sets for raw access or iteration

LIST_BOX_DRAWING = [
    BOX_LIGHT_HORIZONTAL, BOX_HEAVY_HORIZONTAL, BOX_LIGHT_VERTICAL, BOX_HEAVY_VERTICAL,
    BOX_LIGHT_TRIPLE_DASH_HZ, BOX_HEAVY_TRIPLE_DASH_HZ, BOX_LIGHT_TRIPLE_DASH_VT, BOX_HEAVY_TRIPLE_DASH_VT,
    BOX_LIGHT_QUAD_DASH_HZ, BOX_HEAVY_QUAD_DASH_HZ, BOX_LIGHT_QUAD_DASH_VT, BOX_HEAVY_QUAD_DASH_VT,
    BOX_LIGHT_DOWN_RIGHT, BOX_DOWN_LIGHT_RIGHT_HEAVY, BOX_DOWN_HEAVY_RIGHT_LIGHT, BOX_HEAVY_DOWN_RIGHT,
    BOX_LIGHT_DOWN_LEFT, BOX_DOWN_LIGHT_LEFT_HEAVY, BOX_DOWN_HEAVY_LEFT_LIGHT, BOX_HEAVY_DOWN_LEFT,
    BOX_LIGHT_UP_RIGHT, BOX_UP_LIGHT_RIGHT_HEAVY, BOX_UP_HEAVY_RIGHT_LIGHT, BOX_HEAVY_UP_RIGHT,
    BOX_LIGHT_UP_LEFT, BOX_UP_LIGHT_LEFT_HEAVY, BOX_UP_HEAVY_LEFT_LIGHT, BOX_HEAVY_UP_LEFT,
    BOX_LIGHT_VERTICAL_RIGHT, BOX_HEAVY_VERTICAL_RIGHT, BOX_LIGHT_VERTICAL_LEFT, BOX_HEAVY_VERTICAL_LEFT,
    BOX_LIGHT_DOWN_HORIZONTAL, BOX_HEAVY_DOWN_HORIZONTAL, BOX_LIGHT_UP_HORIZONTAL, BOX_HEAVY_UP_HORIZONTAL,
    BOX_LIGHT_CROSS, BOX_HEAVY_CROSS,
    BOX_LIGHT_DOUBLE_DASH_HZ, BOX_HEAVY_DOUBLE_DASH_HZ, BOX_LIGHT_DOUBLE_DASH_VT, BOX_HEAVY_DOUBLE_DASH_VT,
    BOX_DOUBLE_HORIZONTAL, BOX_DOUBLE_VERTICAL, BOX_DOUBLE_DOWN_RIGHT, BOX_DOUBLE_DOWN_LEFT,
    BOX_DOUBLE_UP_RIGHT, BOX_DOUBLE_UP_LEFT, BOX_DOUBLE_VERTICAL_RIGHT, BOX_DOUBLE_VERTICAL_LEFT,
    BOX_DOUBLE_DOWN_HORIZONTAL, BOX_DOUBLE_UP_HORIZONTAL, BOX_DOUBLE_CROSS,
    BOX_ARC_DOWN_RIGHT, BOX_ARC_DOWN_LEFT, BOX_ARC_UP_LEFT, BOX_ARC_UP_RIGHT,
    BOX_DIAGONAL_UP_RIGHT, BOX_DIAGONAL_UP_LEFT, BOX_DIAGONAL_CROSS,
]

LIST_BLOCK_ELEMENTS = [
    BLOCK_UPPER_HALF, '▁', BLOCK_LOWER_2_8, BLOCK_LOWER_3_8, BLOCK_LOWER_4_8, BLOCK_LOWER_5_8, BLOCK_LOWER_6_8, BLOCK_LOWER_7_8, BLOCK_FULL,
    BLOCK_LEFT_7_8, BLOCK_LEFT_6_8, BLOCK_LEFT_5_8, BLOCK_LEFT_4_8, BLOCK_LEFT_3_8, BLOCK_LEFT_2_8, BLOCK_LEFT_1_8, '▐',
    BLOCK_SHADE_LIGHT, BLOCK_SHADE_MEDIUM, BLOCK_SHADE_DARK, '▔', '▕',
    BLOCK_QUAD_LOWER_LEFT, BLOCK_QUAD_LOWER_RIGHT, BLOCK_QUAD_UPPER_LEFT, '▙', '▚', '▛', '▜', BLOCK_QUAD_UPPER_RIGHT, '▞', '▟',
]

LIST_GEOMETRIC_SHAPES = [
    '■', '□', '▢', '▣', '▤', '▥', '▦', '▧', '▨', '▩', '▪', '▫', '▬', '▭', '▮', '▯',
    '▰', '▱', TRIANGLE_UP, '△', TRIANGLE_UP_SMALL, '▵', TRIANGLE_RIGHT, '▷', TRIANGLE_RIGHT_SMALL, '▹', '►', '▻', TRIANGLE_DOWN, '▽', TRIANGLE_DOWN_SMALL, '▿',
    TRIANGLE_LEFT, '◁', TRIANGLE_LEFT_SMALL, '◃', '◄', '◅', '◆', '◇', '◈', ICON_RADIO_ON, '◊', ICON_RADIO_OFF, '◌', '◍', '◎', '●',
    '◐', '◑', '◒', '◓', '◔', '◕', '◖', '◗', '◘', '◙', '◚', '◛', '◜', '◝', '◞', '◟',
    '◠', '◡', '◢', '◣', '◤', '◥', '◦', '◧', '◨', '◩', '◪', '◫', '◬', '◭', '◮', '◯',
    '◰', '◱', '◲', '◳', '◴', '◵', '◶', '◷', '◸', '◹', '◺', '◻', '◼', '◽', '◾', '◿',
]

LIST_ARROWS = [
    ARROW_LEFT, ARROW_UP, ARROW_RIGHT, ARROW_DOWN, ARROW_LEFT_RIGHT, ARROW_UP_DOWN, '↖', '↗', '↘', '↙', '↚', '↛', '↜', '↝', '↞', '↟',
    '↠', '↡', '↢', '↣', '↤', '↥', '↦', '↧', '↨', '↩', '↪', '↫', '↬', '↭', '↮', '↯',
    '↰', '↱', '↲', '↳', '↴', '↵', '↶', '↷', '↸', '↹', '↺', '↻', '↼', '↽', '↾', '↿',
    '⇀', '⇁', '⇂', '⇃', '⇄', '⇅', '⇆', '⇇', '⇈', '⇉', '⇊', '⇋', '⇌', '⇍', '⇎', '⇏',
    '⇐', '⇑', '⇒', '⇓', '⇔', '⇕', '⇖', '⇗', '⇘', '⇙', '⇚', '⇛', '⇜', '⇝', '⇞', '⇟',
    '⇠', '⇡', '⇢', '⇣', '⇤', '⇥', '⇦', '⇧', '⇨', '⇩', '⇪', '⇫', '⇬', '⇭', '⇮', '⇯',
    '⇰', '⇱', '⇲', '⇳', '⇴', '⇵', '⇶', '⇷', '⇸', '⇹', '⇺', '⇻', '⇼', '⇽', '⇾', '⇿',
]

LIST_MISC_SYMBOLS = [
    '☀', '☁', '☂', '☃', '☄', ICON_STAR_FILLED, ICON_STAR_EMPTY, '☇', '☈', '☉', '☊', '☋', '☌', '☍', '☎', '☏',
    ICON_CHECKBOX_OFF, ICON_CHECKBOX_ON, '☒', '☓', '☔', '☕', '☖', '☗', '☘', '☙', '☚', '☛', '☜', '☝', '☞', '☟',
    '☠', '☡', '☢', '☣', '☤', '☥', '☦', '☧', '☨', '☩', '☪', '☫', '☬', '☭', '☮', '☯',
    '☰', '☱', '☲', '☳', '☴', '☵', '☶', '☷', '☸', '☹', '☺', '☻', '☼', '☽', '☾', '☿',
    '♀', '♁', '♂', '♃', '♄', '♅', '♆', '♇', '♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏',
    '♐', '♑', '♒', '♓', '♔', '♕', '♖', '♗', '♘', '♙', '♚', '♛', '♜', '♝', '♞', '♟',
    '♠', ICON_HEART_EMPTY, '♢', '♣', '♤', ICON_HEART_FILLED, '♦', '♧', '♨', '♩', '♪', '♫', '♬', '♭', '♮', '♯',
    '♰', '♱', '♲', '♳', '♴', '♵', '♶', '♷', '♸', '♹', '♺', '♻', '♼', '♽', '♾', '♿',
    '⚀', '⚁', '⚂', '⚃', '⚄', '⚅', '⚆', '⚇', '⚈', '⚉', '⚊', '⚋', '⚌', '⚍', '⚎', '⚏',
    '⚐', '⚑', '⚒', '⚓', '⚔', '⚕', '⚖', '⚗', '⚘', ICON_SETTINGS, '⚚', '⚛', '⚜', '⚝', '⚞', '⚟',
    ICON_WARNING, '⚡', '⚢', '⚣', '⚤', '⚥', '⚦', '⚧', '⚨', '⚩', '⚪', '⚫', '⚬', '⚭', '⚮', '⚯',
    '⚰', '⚱', '⚲', '⚳', '⚴', '⚵', '⚶', '⚷', '⚸', '⚹', '⚺', '⚻', '⚼', '⚽', '⚾', '⚿',
    '⛀', '⛁', '⛂', '⛃', '⛄', '⛅', '⛆', '⛇', '⛈', '⛉', '⛊', '⛋', '⛌', '⛍', '⛎', '⛏',
    '⛐', '⛑', '⛒', '⛓', ICON_ERROR, '⛕', '⛖', '⛗', '⛘', '⛙', '⛚', '⛛', '⛜', '⛝', '⛞', '⛟',
    '⛠', '⛡', '⛢', '⛣', '⛤', '⛥', '⛦', '⛧', '⛨', '⛩', '⛪', '⛫', '⛬', '⛭', '⛮', '⛯',
    '⛰', '⛱', '⛲', '⛳', '⛴', '⛵', '⛶', '⛷', '⛸', '⛹', '⛺', '⛻', '⛼', '⛽', '⛾', '⛿',
]

LIST_DINGBATS = [
    '✀', '✁', '✂', '✃', ICON_DELETE, '✅', '✆', '✇', '✈', ICON_MAIL, '✊', '✋', '✌', '✍', ICON_EDIT, '✏',
    '✐', '✑', '✒', '✓', ICON_CHECK, '✕', '✖', '✗', ICON_CROSS, '✙', '✚', '✛', '✜', '✝', '✞', '✟',
    '✠', '✡', '✢', '✣', '✤', '✥', '✦', '✧', '✨', '✩', '✪', '✫', '✬', '✭', '✮', '✯',
    '✰', '✱', '✲', '✳', '✴', '✵', '✶', '✷', '✸', '✹', '✺', '✻', '✼', '✽', '✾', '✿',
    '❀', '❁', '❂', '❃', '❄', '❅', '❆', '❇', '❈', '❉', '❊', '❋', '❌', '❍', '❎', '❏',
    '❐', '❑', '❒', '❓', '❔', '❕', '❖', '❗', '❘', '❙', '❚', '❛', '❜', '❝', '❞', '❟',
    '❠', '❡', '❢', '❣', '❤', '❥', '❦', '❧', '❨', '❩', '❪', '❫', '❬', '❭', '❮', '❯',
    '❰', '❱', '❲', '❳', '❴', '❵', '❶', '❷', '❸', '❹', '❺', '❻', '❼', '❽', '❾', '❿',
    '➀', '➁', '➂', '➃', '➄', '➅', '➆', '➇', '➈', '➉', '➊', '➋', '➌', '➍', '➎', '➏',
    '➐', '➑', '➒', '➓', '➔', '➕', '➖', '➗', '➘', '➙', '➚', '➛', '➜', '➝', '➞', '➟',
    '➠', '➡', '➢', '➣', '➤', '➥', '➦', '➧', '➨', '➩', '➪', '➫', '➬', '➭', '➮', '➯',
    '➰', '➱', '➲', '➳', '➴', '➵', '➶', '➷', '➸', '➹', '➺', '➻', '➼', '➽', '➾', '➿',
]

LIST_BRAILLE = [
    '⠀', '⠁', '⠂', '⠃', '⠄', '⠅', '⠆', '⠇', '⠈', '⠉', '⠊', '⠋', '⠌', '⠍', '⠎', '⠏',
    '⠐', '⠑', '⠒', '⠓', '⠔', '⠕', '⠖', '⠗', '⠘', '⠙', '⠚', '⠛', '⠜', '⠝', '⠞', '⠟',
    '⠠', '⠡', '⠢', '⠣', '⠤', '⠥', '⠦', '⠧', '⠨', '⠩', '⠪', '⠫', '⠬', '⠭', '⠮', '⠯',
    '⠰', '⠱', '⠲', '⠳', '⠴', '⠵', '⠶', '⠷', '⠸', '⠹', '⠺', '⠻', '⠼', '⠽', '⠾', '⠿',
    '⡀', '⡁', '⡂', '⡃', '⡄', '⡅', '⡆', '⡇', '⡈', '⡉', '⡊', '⡋', '⡌', '⡍', '⡎', '⡏',
    '⡐', '⡑', '⡒', '⡓', '⡔', '⡕', '⡖', '⡗', '⡘', '⡙', '⡚', '⡛', '⡜', '⡝', '⡞', '⡟',
    '⡠', '⡡', '⡢', '⡣', '⡤', '⡥', '⡦', '⡧', '⡨', '⡩', '⡪', '⡫', '⡬', '⡭', '⡮', '⡯',
    '⡰', '⡱', '⡲', '⡳', '⡴', '⡵', '⡶', '⡷', '⡸', '⡹', '⡺', '⡻', '⡼', '⡽', '⡾', '⡿',
    '⢀', '⢁', '⢂', '⢃', '⢄', '⢅', '⢆', '⢇', '⢈', '⢉', '⢊', '⢋', '⢌', '⢍', '⢎', '⢏',
    '⢐', '⢑', '⢒', '⢓', '⢔', '⢕', '⢖', '⢗', '⢘', '⢙', '⢚', '⢛', '⢜', '⢝', '⢞', '⢟',
    '⢠', '⢡', '⢢', '⢣', '⢤', '⢥', '⢦', '⢧', '⢨', '⢩', '⢪', '⢫', '⢬', '⢭', '⢮', '⢯',
    '⢰', '⢱', '⢲', '⢳', '⢴', '⢵', '⢶', '⢷', '⢸', '⢹', '⢺', '⢻', '⢼', '⢽', '⢾', '⢿',
    '⣀', '⣁', '⣂', '⣃', '⣄', '⣅', '⣆', '⣇', '⣈', '⣉', '⣊', '⣋', '⣌', '⣍', '⣎', '⣏',
    '⣐', '⣑', '⣒', '⣓', '⣔', '⣕', '⣖', '⣗', '⣘', '⣙', '⣚', '⣛', '⣜', '⣝', '⣞', '⣟',
    '⣠', '⣡', '⣢', '⣣', '⣤', '⣥', '⣦', '⣧', '⣨', '⣩', '⣪', '⣫', '⣬', '⣭', '⣮', '⣯',
    '⣰', '⣱', '⣲', '⣳', '⣴', '⣵', '⣶', '⣷', '⣸', '⣹', '⣺', '⣻', '⣼', '⣽', '⣾', '⣿',
]

LIST_MATH_OPERATORS = [
    '∀', '∁', '∂', '∃', '∄', '∅', '∆', '∇', '∈', '∉', '∊', '∋', '∌', '∍', '∎', '∏',
    '∐', '∑', '−', '∓', '∔', '∕', '∖', '∗', '∘', '∙', '√', '∛', '∜', '∝', '∞', '∟',
    '∠', '∡', '∢', '∣', '∤', '∥', '∦', '∧', '∨', '∩', '∪', '∫', '∬', '∭', '∮', '∯',
    '∰', '∱', '∲', '∳', '∴', '∵', '∶', '∷', '∸', '∹', '∺', '∻', '∼', '∽', '∾', '∿',
    '≀', '≁', '≂', '≃', '≄', '≅', '≆', '≇', '≈', '≉', '≊', '≋', '≌', '≍', '≎', '≏',
    '≐', '≑', '≒', '≓', '≔', '≕', '≖', '≗', '≘', '≙', '≚', '≛', '≜', '≝', '≞', '≟',
    '≠', '≡', '≢', '≣', '≤', '≥', '≦', '≧', '≨', '≩', '≪', '≫', '≬', '≭', '≮', '≯',
    '≰', '≱', '≲', '≳', '≴', '≵', '≶', '≷', '≸', '≹', '≺', '≻', '≼', '≽', '≾', '≿',
    '⊀', '⊁', '⊂', '⊃', '⊄', '⊅', '⊆', '⊇', '⊈', '⊉', '⊊', '⊋', '⊌', '⊍', '⊎', '⊏',
    '⊐', '⊑', '⊒', '⊓', '⊔', '⊕', '⊖', '⊗', '⊘', '⊙', '⊚', '⊛', '⊜', '⊝', '⊞', '⊟',
    '⊠', '⊡', '⊢', '⊣', '⊤', '⊥', '⊦', '⊧', '⊨', '⊩', '⊪', '⊫', '⊬', '⊭', '⊮', '⊯',
    '⊰', '⊱', '⊲', '⊳', '⊴', '⊵', '⊶', '⊷', '⊸', '⊹', '⊺', '⊻', '⊼', '⊽', '⊾', '⊿',
    '⋀', '⋁', '⋂', '⋃', '⋄', '⋅', '⋆', '⋇', '⋈', '⋉', '⋊', '⋋', '⋌', '⋍', '⋎', '⋏',
    '⋐', '⋑', '⋒', '⋓', '⋔', '⋕', '⋖', '⋗', '⋘', '⋙', '⋚', '⋛', '⋜', '⋝', '⋞', '⋟',
    '⋠', '⋡', '⋢', '⋣', '⋤', '⋥', '⋦', '⋧', '⋨', '⋩', '⋪', '⋫', '⋬', '⋭', '⋮', '⋯',
    '⋰', '⋱', '⋲', '⋳', '⋴', '⋵', '⋶', '⋷', '⋸', '⋹', '⋺', '⋻', '⋼', '⋽', '⋾', '⋿',
]

LIST_ASCII_PRINTABLE = [
    ' ', '!', '"', '#', '$', '%', '&', "'", '(', ')', '*', '+', ',', '-', '.', '/',
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ':', ';', '<', '=', '>', '?',
    '@', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O',
    'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '[', '\\', ']', '^', '_',
    '`', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o',
    'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '{', '|', '}', '~',
]