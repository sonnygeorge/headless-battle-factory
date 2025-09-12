from enum import Enum, IntEnum, IntFlag


class Move(IntEnum):
    """Move IDs - from include/constants/moves.h"""

    NONE = 0
    POUND = 1
    KARATE_CHOP = 2
    DOUBLE_SLAP = 3
    COMET_PUNCH = 4
    MEGA_PUNCH = 5
    PAY_DAY = 6
    FIRE_PUNCH = 7
    ICE_PUNCH = 8
    THUNDER_PUNCH = 9
    SCRATCH = 10
    VICE_GRIP = 11
    GUILLOTINE = 12
    RAZOR_WIND = 13
    SWORDS_DANCE = 14
    CUT = 15
    GUST = 16
    WING_ATTACK = 17
    WHIRLWIND = 18
    FLY = 19
    BIND = 20
    SLAM = 21
    VINE_WHIP = 22
    STOMP = 23
    DOUBLE_KICK = 24
    MEGA_KICK = 25
    JUMP_KICK = 26
    ROLLING_KICK = 27
    SAND_ATTACK = 28
    HEADBUTT = 29
    HORN_ATTACK = 30
    FURY_ATTACK = 31
    HORN_DRILL = 32
    TACKLE = 33
    BODY_SLAM = 34
    WRAP = 35
    TAKE_DOWN = 36
    THRASH = 37
    DOUBLE_EDGE = 38
    TAIL_WHIP = 39
    POISON_STING = 40
    TWINEEDLE = 41
    PIN_MISSILE = 42
    LEER = 43
    BITE = 44
    GROWL = 45
    ROAR = 46
    SING = 47
    SUPERSONIC = 48
    SONIC_BOOM = 49
    DISABLE = 50
    ACID = 51
    EMBER = 52
    FLAMETHROWER = 53
    MIST = 54
    WATER_GUN = 55
    HYDRO_PUMP = 56
    SURF = 57
    ICE_BEAM = 58
    BLIZZARD = 59
    PSYBEAM = 60
    BUBBLE_BEAM = 61
    AURORA_BEAM = 62
    HYPER_BEAM = 63
    PECK = 64
    DRILL_PECK = 65
    SUBMISSION = 66
    LOW_KICK = 67
    COUNTER = 68
    SEISMIC_TOSS = 69
    STRENGTH = 70
    ABSORB = 71
    MEGA_DRAIN = 72
    LEECH_SEED = 73
    GROWTH = 74
    RAZOR_LEAF = 75
    SOLAR_BEAM = 76
    POISON_POWDER = 77
    STUN_SPORE = 78
    SLEEP_POWDER = 79
    PETAL_DANCE = 80
    STRING_SHOT = 81
    DRAGON_RAGE = 82
    FIRE_SPIN = 83
    THUNDER_SHOCK = 84
    THUNDERBOLT = 85
    THUNDER_WAVE = 86
    THUNDER = 87
    ROCK_THROW = 88
    EARTHQUAKE = 89
    FISSURE = 90
    DIG = 91
    TOXIC = 92
    CONFUSION = 93
    PSYCHIC = 94
    HYPNOSIS = 95
    MEDITATE = 96
    AGILITY = 97
    QUICK_ATTACK = 98
    RAGE = 99
    TELEPORT = 100
    NIGHT_SHADE = 101
    MIMIC = 102
    SCREECH = 103
    DOUBLE_TEAM = 104
    RECOVER = 105
    HARDEN = 106
    MINIMIZE = 107
    SMOKESCREEN = 108
    CONFUSE_RAY = 109
    WITHDRAW = 110
    DEFENSE_CURL = 111
    BARRIER = 112
    LIGHT_SCREEN = 113
    HAZE = 114
    REFLECT = 115
    FOCUS_ENERGY = 116
    BIDE = 117
    METRONOME = 118
    MIRROR_MOVE = 119
    SELF_DESTRUCT = 120
    EGG_BOMB = 121
    LICK = 122
    SMOG = 123
    SLUDGE = 124
    BONE_CLUB = 125
    FIRE_BLAST = 126
    WATERFALL = 127
    CLAMP = 128
    SWIFT = 129
    SKULL_BASH = 130
    SPIKE_CANNON = 131
    CONSTRICT = 132
    AMNESIA = 133
    KINESIS = 134
    SOFT_BOILED = 135
    HI_JUMP_KICK = 136
    GLARE = 137
    DREAM_EATER = 138
    POISON_GAS = 139
    BARRAGE = 140
    LEECH_LIFE = 141
    LOVELY_KISS = 142
    SKY_ATTACK = 143
    TRANSFORM = 144
    BUBBLE = 145
    DIZZY_PUNCH = 146
    SPORE = 147
    FLASH = 148
    PSYWAVE = 149
    SPLASH = 150
    ACID_ARMOR = 151
    CRABHAMMER = 152
    EXPLOSION = 153
    FURY_SWIPES = 154
    BONEMERANG = 155
    REST = 156
    ROCK_SLIDE = 157
    HYPER_FANG = 158
    SHARPEN = 159
    CONVERSION = 160
    TRI_ATTACK = 161
    SUPER_FANG = 162
    SLASH = 163
    SUBSTITUTE = 164
    STRUGGLE = 165
    SKETCH = 166
    TRIPLE_KICK = 167
    THIEF = 168
    SPIDER_WEB = 169
    MIND_READER = 170
    NIGHTMARE = 171
    FLAME_WHEEL = 172
    SNORE = 173
    CURSE = 174
    FLAIL = 175
    CONVERSION_2 = 176
    AEROBLAST = 177
    COTTON_SPORE = 178
    REVERSAL = 179
    SPITE = 180
    POWDER_SNOW = 181
    PROTECT = 182
    MACH_PUNCH = 183
    SCARY_FACE = 184
    FAINT_ATTACK = 185
    SWEET_KISS = 186
    BELLY_DRUM = 187
    SLUDGE_BOMB = 188
    MUD_SLAP = 189
    OCTAZOOKA = 190
    SPIKES = 191
    ZAP_CANNON = 192
    FORESIGHT = 193
    DESTINY_BOND = 194
    PERISH_SONG = 195
    ICY_WIND = 196
    DETECT = 197
    BONE_RUSH = 198
    LOCK_ON = 199
    OUTRAGE = 200
    SANDSTORM = 201
    GIGA_DRAIN = 202
    ENDURE = 203
    CHARM = 204
    ROLLOUT = 205
    FALSE_SWIPE = 206
    SWAGGER = 207
    MILK_DRINK = 208
    SPARK = 209
    FURY_CUTTER = 210
    STEEL_WING = 211
    MEAN_LOOK = 212
    ATTRACT = 213
    SLEEP_TALK = 214
    HEAL_BELL = 215
    RETURN = 216
    PRESENT = 217
    FRUSTRATION = 218
    SAFEGUARD = 219
    PAIN_SPLIT = 220
    SACRED_FIRE = 221
    MAGNITUDE = 222
    DYNAMIC_PUNCH = 223
    MEGAHORN = 224
    DRAGON_BREATH = 225
    BATON_PASS = 226
    ENCORE = 227
    PURSUIT = 228
    RAPID_SPIN = 229
    SWEET_SCENT = 230
    IRON_TAIL = 231
    METAL_CLAW = 232
    VITAL_THROW = 233
    MORNING_SUN = 234
    SYNTHESIS = 235
    MOONLIGHT = 236
    HIDDEN_POWER = 237
    CROSS_CHOP = 238
    TWISTER = 239
    RAIN_DANCE = 240
    SUNNY_DAY = 241
    CRUNCH = 242
    MIRROR_COAT = 243
    PSYCH_UP = 244
    EXTREME_SPEED = 245
    ANCIENT_POWER = 246
    SHADOW_BALL = 247
    FUTURE_SIGHT = 248
    ROCK_SMASH = 249
    WHIRLPOOL = 250
    BEAT_UP = 251
    FAKE_OUT = 252
    UPROAR = 253
    STOCKPILE = 254
    SPIT_UP = 255
    SWALLOW = 256
    HEAT_WAVE = 257
    HAIL = 258
    TORMENT = 259
    FLATTER = 260
    WILL_O_WISP = 261
    MEMENTO = 262
    FACADE = 263
    FOCUS_PUNCH = 264
    SMELLING_SALT = 265
    FOLLOW_ME = 266
    NATURE_POWER = 267
    CHARGE = 268
    TAUNT = 269
    HELPING_HAND = 270
    TRICK = 271
    ROLE_PLAY = 272
    WISH = 273
    ASSIST = 274
    INGRAIN = 275
    SUPERPOWER = 276
    MAGIC_COAT = 277
    RECYCLE = 278
    REVENGE = 279
    BRICK_BREAK = 280
    YAWN = 281
    KNOCK_OFF = 282
    ENDEAVOR = 283
    ERUPTION = 284
    SKILL_SWAP = 285
    IMPRISON = 286
    REFRESH = 287
    GRUDGE = 288
    SNATCH = 289
    SECRET_POWER = 290
    DIVE = 291
    ARM_THRUST = 292
    CAMOUFLAGE = 293
    TAIL_GLOW = 294
    LUSTER_PURGE = 295
    MIST_BALL = 296
    FEATHER_DANCE = 297
    TEETER_DANCE = 298
    BLAZE_KICK = 299
    MUD_SPORT = 300
    ICE_BALL = 301
    NEEDLE_ARM = 302
    SLACK_OFF = 303
    HYPER_VOICE = 304
    POISON_FANG = 305
    CRUSH_CLAW = 306
    BLAST_BURN = 307
    HYDRO_CANNON = 308
    METEOR_MASH = 309
    ASTONISH = 310
    WEATHER_BALL = 311
    AROMATHERAPY = 312
    FAKE_TEARS = 313
    AIR_CUTTER = 314
    OVERHEAT = 315
    ODOR_SLEUTH = 316
    ROCK_TOMB = 317
    SILVER_WIND = 318
    METAL_SOUND = 319
    GRASS_WHISTLE = 320
    TICKLE = 321
    COSMIC_POWER = 322
    WATER_SPOUT = 323
    SIGNAL_BEAM = 324
    SHADOW_PUNCH = 325
    EXTRASENSORY = 326
    SKY_UPPERCUT = 327
    SAND_TOMB = 328
    SHEER_COLD = 329
    MUDDY_WATER = 330
    BULLET_SEED = 331
    AERIAL_ACE = 332
    ICICLE_SPEAR = 333
    IRON_DEFENSE = 334
    BLOCK = 335
    HOWL = 336
    DRAGON_CLAW = 337
    FRENZY_PLANT = 338
    BULK_UP = 339
    BOUNCE = 340
    MUD_SHOT = 341
    POISON_TAIL = 342
    COVET = 343
    VOLT_TACKLE = 344
    MAGICAL_LEAF = 345
    WATER_SPORT = 346
    CALM_MIND = 347
    LEAF_BLADE = 348
    DRAGON_DANCE = 349
    ROCK_BLAST = 350
    SHOCK_WAVE = 351
    WATER_PULSE = 352
    DOOM_DESIRE = 353
    PSYCHO_BOOST = 354

    # Special constants
    UNAVAILABLE = 0xFFFF  # Used for checks for moves affected by Disable, Mimic, etc.


class MoveTarget(IntFlag):
    """Move targeting - from include/battle.h"""

    SELECTED = 0  # Choose target manually
    DEPENDS = 1 << 0  # Varies by move
    USER_OR_SELECTED = 1 << 1  # Self or chosen target
    RANDOM = 1 << 2  # Random opponent
    BOTH = 1 << 3  # Both opponents
    USER = 1 << 4  # Self only
    FOES_AND_ALLY = 1 << 5  # All except user
    OPPONENTS_FIELD = 1 << 6  # Opponent's field


class MoveFlag(IntFlag):
    """Move flags - from include/constants/pokemon.h"""

    NONE = 0
    MAKES_CONTACT = 1 << 0  # Physical contact move
    PROTECT_AFFECTED = 1 << 1  # Blocked by Protect/Detect
    MAGIC_COAT_AFFECTED = 1 << 2  # Reflected by Magic Coat
    SNATCH_AFFECTED = 1 << 3  # Can be stolen by Snatch
    MIRROR_MOVE_AFFECTED = 1 << 4  # Can be copied by Mirror Move
    KINGS_ROCK_AFFECTED = 1 << 5  # Can trigger King's Rock flinch

    # =========================================================================
    # MOVE FLAG CHECK METHODS
    # =========================================================================

    def makes_contact(self) -> bool:
        """Check if move makes physical contact (triggers contact abilities/items)"""
        return bool(self & self.MAKES_CONTACT)

    def affected_by_protect(self) -> bool:
        """Check if move is blocked by Protect/Detect"""
        return bool(self & self.PROTECT_AFFECTED)

    def can_be_reflected(self) -> bool:
        """Check if move can be reflected by Magic Coat"""
        return bool(self & self.MAGIC_COAT_AFFECTED)

    def can_be_snatched(self) -> bool:
        """Check if move can be stolen by Snatch"""
        return bool(self & self.SNATCH_AFFECTED)

    def can_be_mirrored(self) -> bool:
        """Check if move can be copied by Mirror Move"""
        return bool(self & self.MIRROR_MOVE_AFFECTED)

    def triggers_kings_rock(self) -> bool:
        """Check if move can trigger King's Rock/Razor Fang flinch"""
        return bool(self & self.KINGS_ROCK_AFFECTED)

    def triggers_contact_abilities(self) -> bool:
        """Check if move triggers contact-based abilities (Static, Flame Body, etc.)"""
        return self.makes_contact()

    def bypasses_protect(self) -> bool:
        """Check if move bypasses Protect/Detect"""
        return not self.affected_by_protect()

    def is_reflectable_status_move(self) -> bool:
        """Check if move is a status move that can be reflected"""
        return self.can_be_reflected()

    def is_priority_blockable(self) -> bool:
        """Check if move can be blocked by priority-blocking moves"""
        return self.affected_by_protect()

    # =========================================================================
    # MOVE FLAG COMBINATION CHECKS
    # =========================================================================

    def has_any_flag(self, *flags: "MoveFlag") -> bool:
        """Check if move has any of the specified flags"""
        combined = MoveFlag.NONE
        for flag in flags:
            combined |= flag
        return bool(self & combined)

    def has_all_flags(self, *flags: "MoveFlag") -> bool:
        """Check if move has all of the specified flags"""
        combined = MoveFlag.NONE
        for flag in flags:
            combined |= flag
        return (self & combined) == combined


class SecondaryEffect(Enum):
    """Secondary move effects - from include/constants/battle.h"""

    NONE = 0
    SLEEP = 1
    POISON = 2
    BURN = 3
    FREEZE = 4
    PARALYSIS = 5
    TOXIC = 6
    CONFUSION = 7
    FLINCH = 8
    TRI_ATTACK = 9
    UPROAR = 10
    PAYDAY = 11
    CHARGING = 12
    WRAP = 13
    RECOIL_25 = 14
    ATK_PLUS_1 = 15
    DEF_PLUS_1 = 16
    SPD_PLUS_1 = 17
    SP_ATK_PLUS_1 = 18
    SP_DEF_PLUS_1 = 19
    ACC_PLUS_1 = 20
    EVS_PLUS_1 = 21
    ATK_MINUS_1 = 22
    DEF_MINUS_1 = 23
    SPD_MINUS_1 = 24
    SP_ATK_MINUS_1 = 25
    SP_DEF_MINUS_1 = 26
    ACC_MINUS_1 = 27
    EVS_MINUS_1 = 28
    RECHARGE = 29
    RAGE = 30
    STEAL_ITEM = 31
    PREVENT_ESCAPE = 32
    NIGHTMARE = 33
    ALL_STATS_UP = 34
    RAPIDSPIN = 35
    REMOVE_PARALYSIS = 36
    ATK_DEF_DOWN = 37
    RECOIL_33 = 38
    ATK_PLUS_2 = 39
    DEF_PLUS_2 = 40
    SPD_PLUS_2 = 41
    SP_ATK_PLUS_2 = 42
    SP_DEF_PLUS_2 = 43
    ACC_PLUS_2 = 44
    EVS_PLUS_2 = 45
    ATK_MINUS_2 = 46
    DEF_MINUS_2 = 47
    SPD_MINUS_2 = 48
    SP_ATK_MINUS_2 = 49
    SP_DEF_MINUS_2 = 50
    ACC_MINUS_2 = 51
    EVS_MINUS_2 = 52
    THRASH = 53
    KNOCK_OFF = 54
    SP_ATK_TWO_DOWN = 59
