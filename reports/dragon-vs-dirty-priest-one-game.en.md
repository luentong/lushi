# Dragon Warrior vs Dirty Priest: Full Action Trace

Fixed seed: 202609140001

1. Player 1: Play [Carrier Whelp]
2. Player 1: End turn
   Global state after turn:
   - P1: HP 30/30, Armor 0, Mana 0/1, Hand 4 [Searing Fissure, Brood Keeper, Erupting Volcano, Timelord Nozdormu], Deck 27, Board [Carrier Whelp (1/2, damage 0)], Weapon [none], Locations [none]
   - P2: HP 40/40, Armor 0, Mana 1/1, Hand 6 [Mind Sweeper, Bitterbloom Knight, Kaldorei Priestess, Sanguine Depths, The Coin, Unshackle Soul], Deck 36, Board [empty], Weapon [none], Locations [none]
3. Player 2: Play [Sanguine Depths]
4. Player 2: Play [The Coin]
5. Player 2: Play [Unshackle Soul] -> [Carrier Whelp]
6. Player 2: End turn
   Global state after turn:
   - P1: HP 30/30, Armor 0, Mana 2/2, Hand 5 [Searing Fissure, Brood Keeper, Erupting Volcano, Timelord Nozdormu, Prescient Slitherdrake], Deck 26, Board [empty], Weapon [none], Locations [none]
   - P2: HP 40/40, Armor 0, Mana 0/1, Hand 3 [Mind Sweeper, Bitterbloom Knight, Kaldorei Priestess], Deck 36, Board [empty], Weapon [none], Locations [Sanguine Depths (durability 3, cooldown 2)]
7. Player 1: Play [Brood Keeper]
8. Player 1: Hero attack -> [Player 2 hero]
9. Player 1: End turn
   Global state after turn:
   - P1: HP 30/30, Armor 0, Mana 0/2, Hand 4 [Searing Fissure, Erupting Volcano, Timelord Nozdormu, Prescient Slitherdrake], Deck 26, Board [Brood Keeper (2/3, damage 0)], Weapon [Brood Keeper's Sword], Locations [none]
   - P2: HP 38/40, Armor 0, Mana 2/2, Hand 4 [Mind Sweeper, Bitterbloom Knight, Kaldorei Priestess, Shadow Word: Ruin], Deck 35, Board [empty], Weapon [none], Locations [Sanguine Depths (durability 3, cooldown 1)]
10. Player 2: Play [Mind Sweeper]
11. Player 2: End turn
   Global state after turn:
   - P1: HP 30/30, Armor 0, Mana 3/3, Hand 5 [Searing Fissure, Erupting Volcano, Timelord Nozdormu, Prescient Slitherdrake, Shadowflame Suffusion], Deck 25, Board [Brood Keeper (2/1, damage 2)], Weapon [Brood Keeper's Sword], Locations [none]
   - P2: HP 38/40, Armor 0, Mana 0/2, Hand 3 [Bitterbloom Knight, Kaldorei Priestess, Shadow Word: Ruin], Deck 35, Board [Mind Sweeper (2/3, damage 0)], Weapon [none], Locations [Sanguine Depths (durability 3, cooldown 1)]
12. Player 1: Hero attack -> [Mind Sweeper]
13. Player 1: Minion attack [Brood Keeper] -> [Mind Sweeper]
14. Player 1: Play [Timelord Nozdormu]
15. Player 1: End turn
   Global state after turn:
   - P1: HP 28/30, Armor 0, Mana 0/3, Hand 4 [Searing Fissure, Erupting Volcano, Prescient Slitherdrake, Shadowflame Suffusion], Deck 25, Board [Timelord Nozdormu (8/8, damage 0, dormant 5)], Weapon [none], Locations [none]
   - P2: HP 38/40, Armor 0, Mana 3/3, Hand 4 [Bitterbloom Knight, Kaldorei Priestess, Shadow Word: Ruin, Searing Fissure], Deck 34, Board [empty], Weapon [none], Locations [Sanguine Depths (durability 3, cooldown 0)]
16. Player 2: Play [Kaldorei Priestess]
17. Player 2: Use location [Sanguine Depths] -> [Kaldorei Priestess]
18. Player 2: End turn
   Global state after turn:
   - P1: HP 28/30, Armor 0, Mana 4/4, Hand 5 [Searing Fissure, Erupting Volcano, Prescient Slitherdrake, Shadowflame Suffusion, Darkrider], Deck 24, Board [Timelord Nozdormu (6/8, damage 0, dormant 4)], Weapon [none], Locations [none]
   - P2: HP 38/40, Armor 0, Mana 0/3, Hand 3 [Bitterbloom Knight, Shadow Word: Ruin, Searing Fissure], Deck 34, Board [Kaldorei Priestess (5/2, damage 1)], Weapon [none], Locations [Sanguine Depths (durability 2, cooldown 2)]
19. Player 1: Play [Shadowflame Suffusion] -> [Kaldorei Priestess]
20. Player 1: Pick Discover [Afflicted Devastator]
21. Player 1: Play [Searing Fissure]
22. Player 1: Hero attack -> [Player 2 hero]
23. Player 1: End turn
   Global state after turn:
   - P1: HP 28/30, Armor 0, Mana 0/4, Hand 4 [Erupting Volcano, Prescient Slitherdrake, Darkrider, Afflicted Devastator], Deck 24, Board [Timelord Nozdormu (8/8, damage 0, dormant 4)], Weapon [none], Locations [none]
   - P2: HP 35/40, Armor 0, Mana 4/4, Hand 4 [Bitterbloom Knight, Shadow Word: Ruin, Searing Fissure, Soothsayer], Deck 33, Board [empty], Weapon [none], Locations [Sanguine Depths (durability 2, cooldown 1)]
24. Player 2: Play [Shadow Word: Ruin]
25. Player 2: Prepare [Soothsayer]
26. Player 2: End turn
   Global state after turn:
   - P1: HP 28/30, Armor 0, Mana 5/5, Hand 5 [Erupting Volcano, Prescient Slitherdrake, Darkrider, Afflicted Devastator, Erupting Volcano], Deck 23, Board [Timelord Nozdormu (8/8, damage 0, dormant 3)], Weapon [none], Locations [none]
   - P2: HP 35/40, Armor 0, Mana 0/4, Hand 3 [Bitterbloom Knight, Searing Fissure, Soothsayer], Deck 33, Board [empty], Weapon [none], Locations [Sanguine Depths (durability 2, cooldown 1)]
27. Player 1: Play [Prescient Slitherdrake]
28. Player 1: Play [Darkrider]
29. Player 1: Pick Discover [Chillmaw]
30. Player 1: End turn
   Global state after turn:
   - P1: HP 28/30, Armor 0, Mana 0/5, Hand 4 [Erupting Volcano, Afflicted Devastator, Erupting Volcano, Chillmaw], Deck 23, Board [Timelord Nozdormu (8/8, damage 0, dormant 2), Prescient Slitherdrake (5/8, damage 0), Darkrider (1/1, damage 0)], Weapon [none], Locations [none]
   - P2: HP 35/40, Armor 0, Mana 5/5, Hand 4 [Bitterbloom Knight, Searing Fissure, Soothsayer, Windpeak Wyrm], Deck 32, Board [empty], Weapon [none], Locations [Sanguine Depths (durability 2, cooldown 0)]
31. Player 2: Use location [Sanguine Depths] -> [Darkrider]
32. Player 2: Play [Bitterbloom Knight]
33. Player 2: Play [Searing Fissure]
34. Player 2: Hero attack -> [Prescient Slitherdrake]
35. Player 2: End turn
   Global state after turn:
   - P1: HP 28/30, Armor 0, Mana 6/6, Hand 5 [Erupting Volcano, Afflicted Devastator, Erupting Volcano, Chillmaw, Royal Librarian], Deck 22, Board [Timelord Nozdormu (8/8, damage 0, dormant 1), Prescient Slitherdrake (5/4, damage 4)], Weapon [none], Locations [none]
   - P2: HP 30/40, Armor 0, Mana 1/5, Hand 2 [Soothsayer, Windpeak Wyrm], Deck 32, Board [Bitterbloom Knight (2/2, damage 1)], Weapon [none], Locations [Sanguine Depths (durability 1, cooldown 2)]
36. Player 1: Minion attack [Prescient Slitherdrake] -> [Bitterbloom Knight]
37. Player 1: Play [Afflicted Devastator]
38. Player 1: Minion attack [Afflicted Devastator]
39. Player 1: Use hero power
40. Player 1: End turn
   Global state after turn:
   - P1: HP 28/30, Armor 2, Mana 0/6, Hand 4 [Erupting Volcano, Erupting Volcano, Chillmaw, Royal Librarian], Deck 22, Board [Timelord Nozdormu (8/5, damage 3, dormant 1), Afflicted Devastator (6/6, damage 0)], Weapon [none], Locations [none]
   - P2: HP 24/40, Armor 0, Mana 6/6, Hand 3 [Soothsayer, Windpeak Wyrm, Hook n' Heave], Deck 31, Board [empty], Weapon [none], Locations [Sanguine Depths (durability 1, cooldown 1)]
41. Player 2: Play [Soothsayer]
42. Player 2: End turn
   Global state after turn:
   - P1: HP 28/30, Armor 2, Mana 7/7, Hand 5 [Erupting Volcano, Erupting Volcano, Chillmaw, Royal Librarian, Sanguine Depths], Deck 21, Board [Timelord Nozdormu (8/5, damage 3), Afflicted Devastator (6/6, damage 0)], Weapon [none], Locations [none]
   - P2: HP 24/40, Armor 0, Mana 0/6, Hand 2 [Windpeak Wyrm, Hook n' Heave], Deck 31, Board [Soothsayer (6/6, damage 0)], Weapon [none], Locations [Sanguine Depths (durability 1, cooldown 1)]
43. Player 1: Minion attack [Timelord Nozdormu] -> [Soothsayer]
44. Player 1: Minion attack [Afflicted Devastator] -> [Bonechill Stegodon]
45. Player 1: Play [Chillmaw]
46. Player 1: End turn
   Global state after turn:
   - P1: HP 24/30, Armor 0, Mana 0/7, Hand 4 [Erupting Volcano, Erupting Volcano, Royal Librarian, Sanguine Depths], Deck 21, Board [Chillmaw (9/6, damage 0)], Weapon [none], Locations [none]
   - P2: HP 30/40, Armor 0, Mana 7/7, Hand 3 [Windpeak Wyrm, Hook n' Heave, Darkrider], Deck 30, Board [empty], Weapon [none], Locations [Sanguine Depths (durability 1, cooldown 0)]
47. Player 2: Use location [Sanguine Depths] -> [Chillmaw]
48. Player 2: Play [Hook n' Heave]
49. Player 2: Pick Discover [Time Skipper]
50. Player 2: Play [Time Skipper]
51. Player 2: Play [Darkrider]
52. Player 2: Pick Discover [Runaway Blackwing]
53. Player 2: End turn
   Global state after turn:
   - P1: HP 23/30, Armor 0, Mana 8/8, Hand 5 [Erupting Volcano, Erupting Volcano, Royal Librarian, Sanguine Depths, Darkrider], Deck 20, Board [Chillmaw (11/4, damage 2)], Weapon [none], Locations [none]
   - P2: HP 30/40, Armor 0, Mana 0/7, Hand 3 [Windpeak Wyrm, Runaway Blackwing, The Coin], Deck 30, Board [Cannoneer (1/1, damage 0), Cannoneer (1/1, damage 0), Time Skipper (3/4, damage 0), Darkrider (1/1, damage 0)], Weapon [none], Locations [none]
54. Player 1: Minion attack [Chillmaw] -> [Time Skipper]
55. Player 1: Play [Royal Librarian] -> [Cannoneer]
56. Player 1: Play [Erupting Volcano]
57. Player 1: Play [Darkrider]
58. Player 1: End turn
   Global state after turn:
   - P1: HP 27/30, Armor 0, Mana 0/8, Hand 2 [Erupting Volcano, Sanguine Depths], Deck 20, Board [Chillmaw (11/1, damage 5), Royal Librarian (4/4, damage 0), Darkrider (1/1, damage 0)], Weapon [none], Locations [Erupting Volcano (durability 3, cooldown 2)]
   - P2: HP 30/40, Armor 0, Mana 8/8, Hand 4 [Windpeak Wyrm, Runaway Blackwing, The Coin, Soothsayer], Deck 29, Board [Cannoneer (1/1, damage 0), Cannoneer (1/1, damage 0), Darkrider (1/1, damage 0)], Weapon [none], Locations [none]
59. Player 2: Minion attack [Cannoneer] -> [Chillmaw]
60. Player 2: Minion attack [Cannoneer] -> [Darkrider]
61. Player 2: Minion attack [Darkrider] -> [Royal Librarian]
62. Player 2: Play [Windpeak Wyrm] -> [Royal Librarian]
63. Player 2: Play [The Coin]
64. Player 2: Prepare [Soothsayer]
65. Player 2: End turn
   Global state after turn:
   - P1: HP 28/30, Armor 0, Mana 9/9, Hand 3 [Erupting Volcano, Sanguine Depths, Mother Duck], Deck 19, Board [empty], Weapon [none], Locations [Erupting Volcano (durability 3, cooldown 1)]
   - P2: HP 30/40, Armor 5, Mana 0/8, Hand 2 [Runaway Blackwing, Soothsayer], Deck 29, Board [Windpeak Wyrm (6/6, damage 0)], Weapon [none], Locations [none]
66. Player 1: Play [Mother Duck]
67. Player 1: Minion attack [Duckling] -> [Windpeak Wyrm]
68. Player 1: Minion attack [Duckling] -> [Windpeak Wyrm]
69. Player 1: Minion attack [Duckling] -> [Windpeak Wyrm]
70. Player 1: Play [Erupting Volcano]
71. Player 1: Play [Sanguine Depths]
72. Player 1: End turn
   Global state after turn:
   - P1: HP 28/30, Armor 0, Mana 1/9, Hand 0 [empty], Deck 19, Board [Mother Duck (2/3, damage 0)], Weapon [none], Locations [Erupting Volcano (durability 3, cooldown 1), Erupting Volcano (durability 3, cooldown 2), Sanguine Depths (durability 3, cooldown 2)]
   - P2: HP 30/40, Armor 5, Mana 9/9, Hand 3 [Runaway Blackwing, Soothsayer, Karazhan the Sanctum], Deck 28, Board [Windpeak Wyrm (6/3, damage 3)], Weapon [none], Locations [none]
73. Player 2: Minion attack [Windpeak Wyrm] -> [Mother Duck]
74. Player 2: Play [Soothsayer]
75. Player 2: Use hero power
76. Player 2: Pick Discover [Sinful Steed]
77. Player 2: Play [Sinful Steed]
78. Player 2: End turn
   Global state after turn:
   - P1: HP 28/30, Armor 0, Mana 10/10, Hand 1 [Hook n' Heave], Deck 18, Board [empty], Weapon [none], Locations [Erupting Volcano (durability 3, cooldown 0), Erupting Volcano (durability 3, cooldown 1), Sanguine Depths (durability 3, cooldown 1)]
   - P2: HP 30/40, Armor 5, Mana 0/9, Hand 2 [Runaway Blackwing, Karazhan the Sanctum], Deck 28, Board [Windpeak Wyrm (6/1, damage 5), Soothsayer (6/6, damage 0), Sinful Steed (2/3, damage 0)], Weapon [none], Locations [none]
79. Player 1: Play [Hook n' Heave]
80. Player 1: Pick Discover [Captain Crowley]
81. Player 1: Play [Captain Crowley]
82. Player 1: Use location [Erupting Volcano]
83. Player 1: Use hero power
84. Player 1: End turn
   Global state after turn:
   - P1: HP 28/30, Armor 2, Mana 1/10, Hand 0 [empty], Deck 18, Board [Cannoneer (1/1, damage 0), Cannoneer (1/1, damage 0), Captain Crowley (4/5, damage 0), Cannoneer (1/1, damage 0)], Weapon [none], Locations [Erupting Volcano (durability 2, cooldown 2), Erupting Volcano (durability 3, cooldown 1), Sanguine Depths (durability 3, cooldown 1)]
   - P2: HP 30/40, Armor 3, Mana 10/10, Hand 3 [Runaway Blackwing, Karazhan the Sanctum, Lunarwing Messenger], Deck 27, Board [Soothsayer (6/4, damage 2), Sinful Steed (2/2, damage 1)], Weapon [none], Locations [none]
85. Player 2: Minion attack [Soothsayer] -> [Captain Crowley]
86. Player 2: Minion attack [Sinful Steed] -> [Cannoneer]
87. Player 2: Play [Runaway Blackwing]
88. Player 2: End turn
   Global state after turn:
   - P1: HP 28/30, Armor 2, Mana 10/10, Hand 1 [Hook n' Heave], Deck 17, Board [Cannoneer (1/1, damage 0)], Weapon [none], Locations [Erupting Volcano (durability 2, cooldown 1), Erupting Volcano (durability 3, cooldown 0), Sanguine Depths (durability 3, cooldown 0)]
   - P2: HP 37/40, Armor 3, Mana 0/10, Hand 2 [Karazhan the Sanctum, Lunarwing Messenger], Deck 27, Board [Sinful Steed (2/1, damage 2), Hideous Husk (3/5, damage 0), Runaway Blackwing (13/10, damage 0)], Weapon [none], Locations [none]
89. Player 1: Minion attack [Cannoneer] -> [Sinful Steed]
90. Player 1: Use location [Sanguine Depths] -> [Runaway Blackwing]
91. Player 1: Play [Hook n' Heave]
92. Player 1: Pick Discover [Hookfist-3000]
93. Player 1: Play [Hookfist-3000]
94. Player 1: Use location [Erupting Volcano]
95. Player 1: Use hero power
96. Player 1: End turn
   Global state after turn:
   - P1: HP 28/30, Armor 4, Mana 3/10, Hand 0 [empty], Deck 17, Board [Cannoneer (1/1, damage 0), Cannoneer (1/1, damage 0), Hookfist-3000 (4/3, damage 0)], Weapon [none], Locations [Erupting Volcano (durability 2, cooldown 1), Erupting Volcano (durability 2, cooldown 2), Sanguine Depths (durability 2, cooldown 2)]
   - P2: HP 36/40, Armor 0, Mana 10/10, Hand 3 [Karazhan the Sanctum, Lunarwing Messenger, Warptooth], Deck 26, Board [Hideous Husk (3/5, damage 0), Runaway Blackwing (15/8, damage 2)], Weapon [none], Locations [none]
97. Player 2: Minion attack [Hideous Husk] -> [Hookfist-3000]
98. Player 2: Minion attack [Runaway Blackwing] -> [Cannoneer]
99. Player 2: Play [Karazhan the Sanctum]
100. Player 2: End turn
   Global state after turn:
   - P1: HP 28/30, Armor 4, Mana 10/10, Hand 1 [Cannonmaster], Deck 16, Board [empty], Weapon [none], Locations [Erupting Volcano (durability 2, cooldown 0), Erupting Volcano (durability 2, cooldown 1), Sanguine Depths (durability 2, cooldown 1)]
   - P2: HP 38/40, Armor 0, Mana 0/10, Hand 2 [Lunarwing Messenger, Warptooth], Deck 26, Board [Hideous Husk (3/1, damage 4), Runaway Blackwing (15/7, damage 3)], Weapon [none], Locations [Karazhan the Sanctum (durability 2, cooldown 2)]
101. Player 1: Play [Cannonmaster]
102. Player 1: Play [Cannoneer]
103. Player 1: Use location [Erupting Volcano]
104. Player 1: Use hero power
105. Player 1: End turn
   Global state after turn:
   - P1: HP 28/30, Armor 6, Mana 6/10, Hand 0 [empty], Deck 16, Board [Cannonmaster (3/1, damage 0), Cannoneer (1/1, damage 0)], Weapon [none], Locations [Erupting Volcano (durability 1, cooldown 2), Erupting Volcano (durability 2, cooldown 1), Sanguine Depths (durability 2, cooldown 1)]
   - P2: HP 36/40, Armor 0, Mana 10/10, Hand 3 [Lunarwing Messenger, Warptooth, Medivh the Hallowed], Deck 25, Board [Runaway Blackwing (15/6, damage 4)], Weapon [none], Locations [Karazhan the Sanctum (durability 2, cooldown 1)]
106. Player 2: Minion attack [Runaway Blackwing] -> [Cannonmaster]
107. Player 2: Play [Medivh the Hallowed]
108. Player 2: Play [Warptooth]
109. Player 2: Minion attack [Warptooth]
110. Player 2: Play [Lunarwing Messenger]
111. Player 2: Use hero power
112. Player 2: Pick Discover [Mind Sweeper]
113. Player 2: Play [Mind Sweeper]
114. Player 2: End turn
   Global state after turn:
   - P1: HP 28/30, Armor 3, Mana 10/10, Hand 1 [Windpeak Wyrm], Deck 15, Board [empty], Weapon [none], Locations [Erupting Volcano (durability 1, cooldown 1), Erupting Volcano (durability 2, cooldown 0), Sanguine Depths (durability 2, cooldown 0)]
   - P2: HP 37/40, Armor 0, Mana 1/10, Hand 0 [empty], Deck 25, Board [Medivh the Hallowed (7/7, damage 0), Warptooth (3/3, damage 0), Lunarwing Messenger (3/2, damage 0), Mind Sweeper (2/3, damage 0)], Weapon [none], Locations [Karazhan the Sanctum (durability 2, cooldown 1)]
115. Player 1: Play [Windpeak Wyrm] -> [Medivh the Hallowed]
116. Player 1: Use location [Sanguine Depths] -> [Windpeak Wyrm]
117. Player 1: Use location [Erupting Volcano]
118. Player 1: Use hero power
119. Player 1: End turn
   Global state after turn:
   - P1: HP 28/30, Armor 10, Mana 0/10, Hand 0 [empty], Deck 15, Board [Windpeak Wyrm (8/5, damage 1)], Weapon [none], Locations [Erupting Volcano (durability 1, cooldown 1), Erupting Volcano (durability 1, cooldown 2), Sanguine Depths (durability 1, cooldown 2)]
   - P2: HP 35/40, Armor 0, Mana 10/10, Hand 1 [Bitterbloom Knight], Deck 24, Board [Medivh the Hallowed (7/2, damage 5), Warptooth (3/3, damage 0), Lunarwing Messenger (3/2, damage 0), Mind Sweeper (2/2, damage 1)], Weapon [none], Locations [Karazhan the Sanctum (durability 2, cooldown 0)]
120. Player 2: Minion attack [Medivh the Hallowed] -> [Windpeak Wyrm]
121. Player 2: Minion attack [Warptooth]
122. Player 2: Minion attack [Lunarwing Messenger]
123. Player 2: Minion attack [Mind Sweeper]
124. Player 2: Play [Bitterbloom Knight]
125. Player 2: Use location [Karazhan the Sanctum]
126. Player 2: Use hero power
127. Player 2: Pick Discover [Sinful Steed]
128. Player 2: End turn
   Global state after turn:
   - P1: HP 28/30, Armor 2, Mana 10/10, Hand 1 [Cannonmaster], Deck 14, Board [empty], Weapon [none], Locations [Erupting Volcano (durability 1, cooldown 0), Erupting Volcano (durability 1, cooldown 1), Sanguine Depths (durability 1, cooldown 1)]
   - P2: HP 38/40, Armor 0, Mana 6/10, Hand 0 [empty], Deck 24, Board [Warptooth (3/3, damage 0), Lunarwing Messenger (3/2, damage 0), Mind Sweeper (2/2, damage 1), Bitterbloom Knight (2/3, damage 0), Mo'arg Forgefiend (8/8, damage 0), Crumblecrusher (8/6, damage 0)], Weapon [none], Locations [Karazhan the Sanctum (durability 1, cooldown 2)]
129. Player 1: Play [Cannonmaster]
130. Player 1: Play [Cannoneer]
131. Player 1: Use location [Erupting Volcano]
132. Player 1: Use hero power
133. Player 1: End turn
   Global state after turn:
   - P1: HP 28/30, Armor 4, Mana 6/10, Hand 0 [empty], Deck 14, Board [Cannonmaster (3/1, damage 0), Cannoneer (1/1, damage 0)], Weapon [none], Locations [Erupting Volcano (durability 1, cooldown 1), Sanguine Depths (durability 1, cooldown 1)]
   - P2: HP 36/40, Armor 0, Mana 10/10, Hand 1 [Azalina Soulsever], Deck 23, Board [Warptooth (3/3, damage 0), Lunarwing Messenger (3/2, damage 0), Mind Sweeper (2/2, damage 1), Bitterbloom Knight (2/1, damage 2), Mo'arg Forgefiend (8/8, damage 0), Crumblecrusher (8/6, damage 0)], Weapon [none], Locations [Karazhan the Sanctum (durability 1, cooldown 1)]
134. Player 2: Minion attack [Crumblecrusher] -> [Cannonmaster]
135. Player 2: Minion attack [Mo'arg Forgefiend] -> [Cannoneer]
136. Player 2: Minion attack [Warptooth]
137. Player 2: Minion attack [Lunarwing Messenger]
138. Player 2: Minion attack [Mind Sweeper]
139. Player 2: Minion attack [Bitterbloom Knight]
140. Player 2: Use hero power
141. Player 2: Pick Discover [Kaldorei Priestess]
142. Player 2: End turn
   Global state after turn:
   - P1: HP 22/30, Armor 0, Mana 10/10, Hand 1 [Searing Fissure], Deck 13, Board [empty], Weapon [none], Locations [Erupting Volcano (durability 1, cooldown 0), Sanguine Depths (durability 1, cooldown 0)]
   - P2: HP 39/40, Armor 0, Mana 8/10, Hand 1 [Azalina Soulsever], Deck 23, Board [Warptooth (3/3, damage 0), Lunarwing Messenger (3/2, damage 0), Mind Sweeper (2/2, damage 1), Bitterbloom Knight (2/1, damage 2), Mo'arg Forgefiend (8/7, damage 1), Crumblecrusher (8/3, damage 3)], Weapon [none], Locations [Karazhan the Sanctum (durability 1, cooldown 1)]
143. Player 1: Use location [Sanguine Depths] -> [Bitterbloom Knight]
144. Player 1: Play [Searing Fissure]
145. Player 1: Hero attack -> [Mo'arg Forgefiend]
146. Player 1: Use location [Erupting Volcano]
147. Player 1: Use hero power
148. Player 1: End turn
   Global state after turn:
   - P1: HP 14/30, Armor 2, Mana 6/10, Hand 0 [empty], Deck 13, Board [empty], Weapon [none], Locations [none]
   - P2: HP 37/40, Armor 0, Mana 10/10, Hand 2 [Azalina Soulsever, Warptooth], Deck 22, Board [Mind Sweeper (2/1, damage 2), Mo'arg Forgefiend (8/3, damage 5), Crumblecrusher (8/1, damage 5)], Weapon [none], Locations [Karazhan the Sanctum (durability 1, cooldown 0)]
149. Player 2: Minion attack [Crumblecrusher]
150. Player 2: Minion attack [Mo'arg Forgefiend]

Result: 150 actions, 30 turns; winner: Player 2; invalid actions: 0.
