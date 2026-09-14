# Dragon Warrior vs Dirty Priest: Full Action Trace

Fixed seed: 202609140001

1. Player 1: Play [Carrier Whelp]
2. Player 1: End turn
   Global state after turn:
   - P1: HP 30/30, Armor 0, Mana 0/1, Hand 4 [Searing Fissure, Brood Keeper, Erupting Volcano, Timelord Nozdormu], Deck 27, Board [Carrier Whelp (1/2)], Weapon [none], Locations [none]
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
   - P1: HP 30/30, Armor 0, Mana 0/2, Hand 4 [Searing Fissure, Erupting Volcano, Timelord Nozdormu, Prescient Slitherdrake], Deck 26, Board [Brood Keeper (2/3)], Weapon [Brood Keeper's Sword], Locations [none]
   - P2: HP 38/40, Armor 0, Mana 2/2, Hand 4 [Mind Sweeper, Bitterbloom Knight, Kaldorei Priestess, Shadow Word: Ruin], Deck 35, Board [empty], Weapon [none], Locations [Sanguine Depths (durability 3, cooldown 1)]
10. Player 2: Play [Mind Sweeper]
11. Player 2: End turn
   Global state after turn:
   - P1: HP 30/30, Armor 0, Mana 3/3, Hand 5 [Searing Fissure, Erupting Volcano, Timelord Nozdormu, Prescient Slitherdrake, Shadowflame Suffusion], Deck 25, Board [Brood Keeper (2/3)], Weapon [Brood Keeper's Sword], Locations [none]
   - P2: HP 38/40, Armor 0, Mana 0/2, Hand 3 [Bitterbloom Knight, Kaldorei Priestess, Shadow Word: Ruin], Deck 35, Board [Mind Sweeper (2/3)], Weapon [none], Locations [Sanguine Depths (durability 3, cooldown 1)]
12. Player 1: Hero attack -> [Mind Sweeper]
13. Player 1: Minion attack [Brood Keeper] -> [Mind Sweeper]
14. Player 1: Play [Timelord Nozdormu]
15. Player 1: End turn
   Global state after turn:
   - P1: HP 28/30, Armor 0, Mana 0/3, Hand 4 [Searing Fissure, Erupting Volcano, Prescient Slitherdrake, Shadowflame Suffusion], Deck 25, Board [Timelord Nozdormu (8/8)], Weapon [none], Locations [none]
   - P2: HP 38/40, Armor 0, Mana 3/3, Hand 4 [Bitterbloom Knight, Kaldorei Priestess, Shadow Word: Ruin, Searing Fissure], Deck 34, Board [empty], Weapon [none], Locations [Sanguine Depths (durability 3, cooldown 0)]
16. Player 2: Play [Kaldorei Priestess]
17. Player 2: Use location [Sanguine Depths] -> [Kaldorei Priestess]
18. Player 2: End turn
   Global state after turn:
   - P1: HP 28/30, Armor 0, Mana 4/4, Hand 5 [Searing Fissure, Erupting Volcano, Prescient Slitherdrake, Shadowflame Suffusion, Darkrider], Deck 24, Board [Timelord Nozdormu (6/8)], Weapon [none], Locations [none]
   - P2: HP 38/40, Armor 0, Mana 0/3, Hand 3 [Bitterbloom Knight, Shadow Word: Ruin, Searing Fissure], Deck 34, Board [Kaldorei Priestess (5/3)], Weapon [none], Locations [Sanguine Depths (durability 2, cooldown 2)]
19. Player 1: Play [Shadowflame Suffusion] -> [Kaldorei Priestess]
20. Player 1: Pick Discover [Afflicted Devastator]
21. Player 1: Play [Searing Fissure]
22. Player 1: Hero attack -> [Player 2 hero]
23. Player 1: End turn
   Global state after turn:
   - P1: HP 28/30, Armor 0, Mana 0/4, Hand 4 [Erupting Volcano, Prescient Slitherdrake, Darkrider, Afflicted Devastator], Deck 24, Board [Timelord Nozdormu (8/8)], Weapon [none], Locations [none]
   - P2: HP 35/40, Armor 0, Mana 4/4, Hand 4 [Bitterbloom Knight, Shadow Word: Ruin, Searing Fissure, Soothsayer], Deck 33, Board [empty], Weapon [none], Locations [Sanguine Depths (durability 2, cooldown 1)]
24. Player 2: Play [Shadow Word: Ruin]
25. Player 2: Prepare [Soothsayer]
26. Player 2: End turn
   Global state after turn:
   - P1: HP 28/30, Armor 0, Mana 5/5, Hand 5 [Erupting Volcano, Prescient Slitherdrake, Darkrider, Afflicted Devastator, Erupting Volcano], Deck 23, Board [empty], Weapon [none], Locations [none]
   - P2: HP 35/40, Armor 0, Mana 0/4, Hand 3 [Bitterbloom Knight, Searing Fissure, Soothsayer], Deck 33, Board [empty], Weapon [none], Locations [Sanguine Depths (durability 2, cooldown 1)]
27. Player 1: Play [Prescient Slitherdrake]
28. Player 1: Play [Darkrider]
29. Player 1: Pick Discover [Chillmaw]
30. Player 1: End turn
   Global state after turn:
   - P1: HP 28/30, Armor 0, Mana 0/5, Hand 4 [Erupting Volcano, Afflicted Devastator, Erupting Volcano, Chillmaw], Deck 23, Board [Prescient Slitherdrake (5/8), Darkrider (1/1)], Weapon [none], Locations [none]
   - P2: HP 35/40, Armor 0, Mana 5/5, Hand 4 [Bitterbloom Knight, Searing Fissure, Soothsayer, Windpeak Wyrm], Deck 32, Board [empty], Weapon [none], Locations [Sanguine Depths (durability 2, cooldown 0)]
31. Player 2: Use location [Sanguine Depths] -> [Darkrider]
32. Player 2: Play [Bitterbloom Knight]
33. Player 2: Play [Searing Fissure]
34. Player 2: Hero attack -> [Prescient Slitherdrake]
35. Player 2: End turn
   Global state after turn:
   - P1: HP 28/30, Armor 0, Mana 6/6, Hand 5 [Erupting Volcano, Afflicted Devastator, Erupting Volcano, Chillmaw, Royal Librarian], Deck 22, Board [Prescient Slitherdrake (5/8)], Weapon [none], Locations [none]
   - P2: HP 30/40, Armor 0, Mana 1/5, Hand 2 [Soothsayer, Windpeak Wyrm], Deck 32, Board [Bitterbloom Knight (2/3)], Weapon [none], Locations [Sanguine Depths (durability 1, cooldown 2)]
36. Player 1: Minion attack [Prescient Slitherdrake] -> [Bitterbloom Knight]
37. Player 1: Play [Afflicted Devastator]
38. Player 1: Minion attack [Afflicted Devastator]
39. Player 1: Use hero power
40. Player 1: End turn
   Global state after turn:
   - P1: HP 28/30, Armor 2, Mana 0/6, Hand 4 [Erupting Volcano, Erupting Volcano, Chillmaw, Royal Librarian], Deck 22, Board [Afflicted Devastator (6/6)], Weapon [none], Locations [none]
   - P2: HP 24/40, Armor 0, Mana 6/6, Hand 3 [Soothsayer, Windpeak Wyrm, Hook n' Heave], Deck 31, Board [empty], Weapon [none], Locations [Sanguine Depths (durability 1, cooldown 1)]
41. Player 2: Play [Soothsayer]
42. Player 2: End turn
   Global state after turn:
   - P1: HP 28/30, Armor 2, Mana 7/7, Hand 5 [Erupting Volcano, Erupting Volcano, Chillmaw, Royal Librarian, Sanguine Depths], Deck 21, Board [Afflicted Devastator (6/6)], Weapon [none], Locations [none]
   - P2: HP 24/40, Armor 0, Mana 0/6, Hand 2 [Windpeak Wyrm, Hook n' Heave], Deck 31, Board [Soothsayer (6/6)], Weapon [none], Locations [Sanguine Depths (durability 1, cooldown 1)]
43. Player 1: Minion attack [Afflicted Devastator] -> [Soothsayer]
44. Player 1: Play [Chillmaw]
45. Player 1: End turn
   Global state after turn:
   - P1: HP 28/30, Armor 2, Mana 0/7, Hand 4 [Erupting Volcano, Erupting Volcano, Royal Librarian, Sanguine Depths], Deck 21, Board [Chillmaw (9/6)], Weapon [none], Locations [none]
   - P2: HP 30/40, Armor 0, Mana 7/7, Hand 3 [Windpeak Wyrm, Hook n' Heave, Darkrider], Deck 30, Board [Bonechill Stegodon (6/3)], Weapon [none], Locations [Sanguine Depths (durability 1, cooldown 0)]
46. Player 2: Minion attack [Bonechill Stegodon] -> [Chillmaw]
47. Player 2: Play [Hook n' Heave]
48. Player 2: Pick Discover [Time Skipper]
49. Player 2: Play [Time Skipper]
50. Player 2: Use location [Sanguine Depths] -> [Time Skipper]
51. Player 2: Play [Darkrider]
52. Player 2: Pick Discover [Runaway Blackwing]
53. Player 2: End turn
   Global state after turn:
   - P1: HP 24/30, Armor 0, Mana 8/8, Hand 5 [Erupting Volcano, Erupting Volcano, Royal Librarian, Sanguine Depths, Darkrider], Deck 20, Board [empty], Weapon [none], Locations [none]
   - P2: HP 30/40, Armor 0, Mana 0/7, Hand 3 [Windpeak Wyrm, Runaway Blackwing, The Coin], Deck 30, Board [Cannoneer (1/1), Cannoneer (1/1), Time Skipper (5/4), Darkrider (1/1)], Weapon [none], Locations [none]
54. Player 1: Play [Royal Librarian] -> [Time Skipper]
55. Player 1: Play [Erupting Volcano]
56. Player 1: Play [Darkrider]
57. Player 1: End turn
   Global state after turn:
   - P1: HP 24/30, Armor 0, Mana 0/8, Hand 2 [Erupting Volcano, Sanguine Depths], Deck 20, Board [Royal Librarian (4/4), Darkrider (1/1)], Weapon [none], Locations [Erupting Volcano (durability 3, cooldown 2)]
   - P2: HP 30/40, Armor 0, Mana 8/8, Hand 4 [Windpeak Wyrm, Runaway Blackwing, The Coin, Soothsayer], Deck 29, Board [Cannoneer (1/1), Cannoneer (1/1), Time Skipper (3/4), Darkrider (1/1)], Weapon [none], Locations [none]
58. Player 2: Minion attack [Time Skipper] -> [Darkrider]
59. Player 2: Minion attack [Cannoneer] -> [Royal Librarian]
60. Player 2: Minion attack [Cannoneer] -> [Royal Librarian]
61. Player 2: Minion attack [Darkrider] -> [Royal Librarian]
62. Player 2: Minion attack [Warptooth] -> [Royal Librarian]
63. Player 2: Minion attack [Warptooth]
64. Player 2: Play [Windpeak Wyrm]
65. Player 2: Play [The Coin]
66. Player 2: Prepare [Soothsayer]
67. Player 2: End turn
   Global state after turn:
   - P1: HP 16/30, Armor 0, Mana 9/9, Hand 3 [Erupting Volcano, Sanguine Depths, Mother Duck], Deck 19, Board [empty], Weapon [none], Locations [Erupting Volcano (durability 3, cooldown 1)]
   - P2: HP 30/40, Armor 5, Mana 0/8, Hand 2 [Runaway Blackwing, Soothsayer], Deck 27, Board [Time Skipper (3/4), Warptooth (3/3), Windpeak Wyrm (6/6)], Weapon [none], Locations [none]
68. Player 1: Play [Mother Duck]
69. Player 1: Minion attack [Duckling] -> [Windpeak Wyrm]
70. Player 1: Minion attack [Duckling] -> [Windpeak Wyrm]
71. Player 1: Minion attack [Duckling] -> [Windpeak Wyrm]
72. Player 1: Play [Erupting Volcano]
73. Player 1: Play [Sanguine Depths]
74. Player 1: End turn
   Global state after turn:
   - P1: HP 16/30, Armor 0, Mana 1/9, Hand 0 [empty], Deck 19, Board [Mother Duck (2/3)], Weapon [none], Locations [Erupting Volcano (durability 3, cooldown 1), Erupting Volcano (durability 3, cooldown 2), Sanguine Depths (durability 3, cooldown 2)]
   - P2: HP 30/40, Armor 5, Mana 9/9, Hand 3 [Runaway Blackwing, Soothsayer, Karazhan the Sanctum], Deck 26, Board [Time Skipper (3/4), Warptooth (3/3), Windpeak Wyrm (6/6)], Weapon [none], Locations [none]
75. Player 2: Minion attack [Windpeak Wyrm] -> [Mother Duck]
76. Player 2: Minion attack [Time Skipper]
77. Player 2: Minion attack [Warptooth]
78. Player 2: Play [Soothsayer]
79. Player 2: Use hero power
80. Player 2: Pick Discover [Sinful Steed]
81. Player 2: Play [Sinful Steed]
82. Player 2: End turn
   Global state after turn:
   - P1: HP 10/30, Armor 0, Mana 10/10, Hand 1 [Hook n' Heave], Deck 18, Board [empty], Weapon [none], Locations [Erupting Volcano (durability 3, cooldown 0), Erupting Volcano (durability 3, cooldown 1), Sanguine Depths (durability 3, cooldown 1)]
   - P2: HP 30/40, Armor 5, Mana 0/9, Hand 2 [Runaway Blackwing, Karazhan the Sanctum], Deck 26, Board [Time Skipper (3/4), Warptooth (3/3), Windpeak Wyrm (6/6), Soothsayer (6/6), Sinful Steed (2/3)], Weapon [none], Locations [none]
83. Player 1: Play [Hook n' Heave]
84. Player 1: Pick Discover [Captain Crowley]
85. Player 1: Play [Captain Crowley]
86. Player 1: Use location [Erupting Volcano]
87. Player 1: Use hero power
88. Player 1: End turn
   Global state after turn:
   - P1: HP 10/30, Armor 2, Mana 1/10, Hand 0 [empty], Deck 18, Board [Cannoneer (1/1), Cannoneer (1/1), Captain Crowley (4/5), Cannoneer (1/1)], Weapon [none], Locations [Erupting Volcano (durability 2, cooldown 2), Erupting Volcano (durability 3, cooldown 1), Sanguine Depths (durability 3, cooldown 1)]
   - P2: HP 30/40, Armor 3, Mana 10/10, Hand 3 [Runaway Blackwing, Karazhan the Sanctum, Lunarwing Messenger], Deck 25, Board [Time Skipper (3/4), Warptooth (3/3), Soothsayer (6/6), Sinful Steed (2/3)], Weapon [none], Locations [none]
89. Player 2: Minion attack [Soothsayer] -> [Captain Crowley]
90. Player 2: Minion attack [Sinful Steed] -> [Cannoneer]
91. Player 2: Minion attack [Warptooth] -> [Cannoneer]
92. Player 2: Minion attack [Time Skipper] -> [Cannoneer]
93. Player 2: Play [Runaway Blackwing]
94. Player 2: End turn
   Global state after turn:
   - P1: HP 10/30, Armor 2, Mana 10/10, Hand 1 [Hook n' Heave], Deck 17, Board [empty], Weapon [none], Locations [Erupting Volcano (durability 2, cooldown 1), Erupting Volcano (durability 3, cooldown 0), Sanguine Depths (durability 3, cooldown 0)]
   - P2: HP 36/40, Armor 3, Mana 0/10, Hand 2 [Karazhan the Sanctum, Lunarwing Messenger], Deck 25, Board [Warptooth (3/3), Sinful Steed (2/3), Bonechill Stegodon (6/3), Runaway Blackwing (13/10)], Weapon [none], Locations [none]
95. Player 1: Use location [Sanguine Depths] -> [Warptooth]
96. Player 1: Play [Hook n' Heave]
97. Player 1: Pick Discover [Time Skipper]
98. Player 1: Play [Time Skipper]
99. Player 1: Use location [Erupting Volcano]
100. Player 1: Use hero power
101. Player 1: End turn
   Global state after turn:
   - P1: HP 10/30, Armor 4, Mana 2/10, Hand 1 [The Coin], Deck 17, Board [Cannoneer (1/1), Cannoneer (1/1), Time Skipper (3/4)], Weapon [none], Locations [Erupting Volcano (durability 2, cooldown 1), Erupting Volcano (durability 2, cooldown 2), Sanguine Depths (durability 2, cooldown 2)]
   - P2: HP 36/40, Armor 1, Mana 10/10, Hand 3 [Karazhan the Sanctum, Lunarwing Messenger, Medivh the Hallowed], Deck 24, Board [Bonechill Stegodon (6/3), Runaway Blackwing (13/10), Sinful Steed (2/3)], Weapon [none], Locations [none]
102. Player 2: Minion attack [Runaway Blackwing] -> [Time Skipper]
103. Player 2: Minion attack [Sinful Steed] -> [Cannoneer]
104. Player 2: Minion attack [Bonechill Stegodon] -> [Cannoneer]
105. Player 2: Play [Medivh the Hallowed]
106. Player 2: End turn
   Global state after turn:
   - P1: HP 10/30, Armor 4, Mana 10/10, Hand 2 [The Coin, Cannonmaster], Deck 16, Board [empty], Weapon [none], Locations [Erupting Volcano (durability 2, cooldown 0), Erupting Volcano (durability 2, cooldown 1), Sanguine Depths (durability 2, cooldown 1)]
   - P2: HP 40/40, Armor 1, Mana 0/10, Hand 2 [Karazhan the Sanctum, Lunarwing Messenger], Deck 24, Board [Medivh the Hallowed (7/7)], Weapon [none], Locations [none]
107. Player 1: Play [Cannonmaster]
108. Player 1: Play [Cannoneer]
109. Player 1: Play [The Coin]
110. Player 1: Use location [Erupting Volcano]
111. Player 1: Use hero power
112. Player 1: End turn
   Global state after turn:
   - P1: HP 10/30, Armor 6, Mana 7/10, Hand 0 [empty], Deck 16, Board [Cannonmaster (3/1), Cannoneer (1/1)], Weapon [none], Locations [Erupting Volcano (durability 1, cooldown 2), Erupting Volcano (durability 2, cooldown 1), Sanguine Depths (durability 2, cooldown 1)]
   - P2: HP 39/40, Armor 0, Mana 10/10, Hand 3 [Karazhan the Sanctum, Lunarwing Messenger, Bitterbloom Knight], Deck 23, Board [Medivh the Hallowed (7/7)], Weapon [none], Locations [none]
113. Player 2: Minion attack [Medivh the Hallowed] -> [Cannonmaster]
114. Player 2: Play [Karazhan the Sanctum]
115. Player 2: End turn
   Global state after turn:
   - P1: HP 10/30, Armor 6, Mana 10/10, Hand 1 [Windpeak Wyrm], Deck 15, Board [Cannoneer (1/1)], Weapon [none], Locations [Erupting Volcano (durability 1, cooldown 1), Erupting Volcano (durability 2, cooldown 0), Sanguine Depths (durability 2, cooldown 0)]
   - P2: HP 39/40, Armor 0, Mana 0/10, Hand 2 [Lunarwing Messenger, Bitterbloom Knight], Deck 23, Board [Medivh the Hallowed (7/7)], Weapon [none], Locations [Karazhan the Sanctum (durability 2, cooldown 2)]
116. Player 1: Minion attack [Cannoneer] -> [Medivh the Hallowed]
117. Player 1: Play [Windpeak Wyrm] -> [Medivh the Hallowed]
118. Player 1: Use location [Sanguine Depths] -> [Windpeak Wyrm]
119. Player 1: Use location [Erupting Volcano]
120. Player 1: Use hero power
121. Player 1: End turn
   Global state after turn:
   - P1: HP 10/30, Armor 13, Mana 0/10, Hand 0 [empty], Deck 15, Board [Windpeak Wyrm (8/6)], Weapon [none], Locations [Erupting Volcano (durability 1, cooldown 1), Erupting Volcano (durability 1, cooldown 2), Sanguine Depths (durability 1, cooldown 2)]
   - P2: HP 36/40, Armor 0, Mana 10/10, Hand 3 [Lunarwing Messenger, Bitterbloom Knight, Azalina Soulsever], Deck 22, Board [empty], Weapon [none], Locations [Karazhan the Sanctum (durability 2, cooldown 1)]
122. Player 2: Play [Azalina Soulsever]
123. Player 2: Play [Lunarwing Messenger]
124. Player 2: Play [Cannonmaster]
125. Player 2: End turn
   Global state after turn:
   - P1: HP 10/30, Armor 13, Mana 10/10, Hand 1 [Cannonmaster], Deck 14, Board [Windpeak Wyrm (8/6)], Weapon [none], Locations [Erupting Volcano (durability 1, cooldown 0), Erupting Volcano (durability 1, cooldown 1), Sanguine Depths (durability 1, cooldown 1)]
   - P2: HP 36/40, Armor 0, Mana 0/10, Hand 9 [Bitterbloom Knight, Prescient Slitherdrake, Chainbreaker Hogger, Atiesh the Greatstaff, Moonwell, Erupting Volcano, Brood Keeper, Royal Librarian, Cannoneer], Deck 14, Board [Azalina Soulsever (7/7), Lunarwing Messenger (3/2), Cannonmaster (3/1)], Weapon [none], Locations [Karazhan the Sanctum (durability 2, cooldown 1)]
126. Player 1: Minion attack [Windpeak Wyrm] -> [Azalina Soulsever]
127. Player 1: Play [Cannonmaster]
128. Player 1: Play [Cannoneer]
129. Player 1: Use location [Erupting Volcano]
130. Player 1: Use hero power
131. Player 1: End turn
   Global state after turn:
   - P1: HP 10/30, Armor 15, Mana 6/10, Hand 0 [empty], Deck 14, Board [Cannonmaster (3/1), Cannoneer (1/1)], Weapon [none], Locations [Erupting Volcano (durability 1, cooldown 1), Sanguine Depths (durability 1, cooldown 1)]
   - P2: HP 34/40, Armor 0, Mana 10/10, Hand 10 [Bitterbloom Knight, Prescient Slitherdrake, Chainbreaker Hogger, Atiesh the Greatstaff, Moonwell, Erupting Volcano, Brood Keeper, Royal Librarian, Cannoneer, Windpeak Wyrm], Deck 13, Board [Cannonmaster (3/1)], Weapon [none], Locations [Karazhan the Sanctum (durability 2, cooldown 0)]
132. Player 2: Minion attack [Cannonmaster] -> [Cannonmaster]
133. Player 2: Play [Windpeak Wyrm] -> [Cannoneer]
134. Player 2: Play [Brood Keeper]
135. Player 2: Hero attack -> [Player 1 hero]
136. Player 2: Use location [Karazhan the Sanctum]
137. Player 2: End turn
   Global state after turn:
   - P1: HP 10/30, Armor 13, Mana 10/10, Hand 1 [Searing Fissure], Deck 13, Board [empty], Weapon [none], Locations [Erupting Volcano (durability 1, cooldown 0), Sanguine Depths (durability 1, cooldown 0)]
   - P2: HP 34/40, Armor 5, Mana 0/10, Hand 8 [Bitterbloom Knight, Prescient Slitherdrake, Chainbreaker Hogger, Atiesh the Greatstaff, Moonwell, Erupting Volcano, Royal Librarian, Cannoneer], Deck 13, Board [Windpeak Wyrm (6/6), Brood Keeper (2/3), Bronze Keeper (3/7), Windpeak Wyrm (6/6), Sandscale Dragon (6/6)], Weapon [Brood Keeper's Sword], Locations [Karazhan the Sanctum (durability 1, cooldown 2)]
138. Player 1: Use location [Sanguine Depths] -> [Sandscale Dragon]
139. Player 1: Play [Searing Fissure]
140. Player 1: Hero attack -> [Brood Keeper]
141. Player 1: Use location [Erupting Volcano]
142. Player 1: Use hero power
143. Player 1: End turn
   Global state after turn:
   - P1: HP 10/30, Armor 13, Mana 6/10, Hand 0 [empty], Deck 13, Board [empty], Weapon [none], Locations [none]
   - P2: HP 34/40, Armor 4, Mana 10/10, Hand 9 [Bitterbloom Knight, Prescient Slitherdrake, Chainbreaker Hogger, Atiesh the Greatstaff, Moonwell, Erupting Volcano, Royal Librarian, Cannoneer, Moonwell], Deck 12, Board [Windpeak Wyrm (6/6), Bronze Keeper (3/7), Windpeak Wyrm (6/6), Sandscale Dragon (8/6)], Weapon [Brood Keeper's Sword], Locations [Karazhan the Sanctum (durability 1, cooldown 1)]
144. Player 2: Minion attack [Sandscale Dragon]
145. Player 2: Minion attack [Windpeak Wyrm]
146. Player 2: Minion attack [Windpeak Wyrm]
147. Player 2: Minion attack [Bronze Keeper]

Result: 147 actions, 30 turns; winner: Player 2; invalid actions: 0.
