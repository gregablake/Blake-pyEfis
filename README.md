# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/gregablake/Blake-pyEfis/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                    |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|-------------------------------------------------------- | -------: | -------: | -------: | -------: | ------: | --------: |
| src/pyefis/\_\_init\_\_.py                              |        1 |        0 |        0 |        0 |    100% |           |
| src/pyefis/cfg.py                                       |       79 |        0 |       70 |        6 |     96% |49-\>143, 69-\>79, 73-\>79, 80-\>59, 101-\>112, 116-\>88 |
| src/pyefis/common/\_\_init\_\_.py                       |       10 |        0 |        4 |        0 |    100% |           |
| src/pyefis/gui.py                                       |      187 |      187 |       60 |        0 |      0% |    17-281 |
| src/pyefis/hmi/\_\_init\_\_.py                          |       13 |        0 |        2 |        0 |    100% |           |
| src/pyefis/hmi/actionclass.py                           |       29 |        0 |        4 |        0 |    100% |           |
| src/pyefis/hmi/data.py                                  |       75 |       62 |       34 |        0 |     12% |36-64, 68-88, 92-108, 112-116, 120-126 |
| src/pyefis/hmi/functions.py                             |       15 |        0 |        0 |        0 |    100% |           |
| src/pyefis/hmi/keys.py                                  |       50 |       37 |       24 |        0 |     18% |30-49, 52-53, 57-59, 63-65, 69-82 |
| src/pyefis/hmi/menu.py                                  |      176 |      141 |       50 |        0 |     15% |36-84, 87-88, 91-119, 121-125, 128-130, 133, 136-148, 151-157, 160-174, 177-182, 186-200, 203, 206, 209, 212, 215, 218, 221, 226-227, 230-231, 234, 237-240, 243 |
| src/pyefis/hooks.py                                     |       14 |       14 |        4 |        0 |      0% |     17-37 |
| src/pyefis/instruments/NumericalDisplay/\_\_init\_\_.py |      202 |        0 |       42 |        0 |    100% |           |
| src/pyefis/instruments/\_\_init\_\_.py                  |        0 |        0 |        0 |        0 |    100% |           |
| src/pyefis/instruments/ai/VirtualVfr.py                 |      805 |      499 |      244 |       22 |     33% |134-157, 187-\>exit, 191-216, 219-231, 235-436, 440-466, 470-490, 493-497, 500-524, 527-533, 536-542, 545-551, 554-559, 562-\>exit, 572-585, 588, 591, 594, 597, 605-618, 621, 624, 627, 630, 637-656, 659, 662, 665, 668, 674-682, 715, 725-728, 731-735, 738, 750-\>752, 763, 768, 770-\>772, 815, 821-\>819, 835-859, 861, 863, 868-869, 884, 886, 899-905, 914-918, 926-929, 937-947, 956, 958, 966-984, 987-991, 994-998, 1005-1017, 1022-1058 |
| src/pyefis/instruments/ai/\_\_init\_\_.py               |      397 |      109 |       72 |        8 |     67% |47, 127-131, 139-\>142, 164, 181, 238-\>201, 346-\>exit, 349, 362, 366, 372-375, 378, 383-386, 389-392, 395, 398-402, 407, 410, 413, 416, 419, 422, 425-442, 448, 451, 454, 457, 460-472, 478, 481, 484, 487, 490-502, 509-516, 519-539, 542-548 |
| src/pyefis/instruments/airspeed/\_\_init\_\_.py         |      346 |        1 |       72 |        4 |     99% |278-\>280, 294, 517-\>520, 533-\>exit |
| src/pyefis/instruments/altimeter/\_\_init\_\_.py        |      262 |        1 |       40 |        1 |     99% |       111 |
| src/pyefis/instruments/button/\_\_init\_\_.py           |      245 |        0 |      104 |        2 |     99% |266-\>243, 316-\>318 |
| src/pyefis/instruments/gauges/\_\_init\_\_.py           |        6 |        0 |        0 |        0 |    100% |           |
| src/pyefis/instruments/gauges/abstract.py               |      451 |      211 |      168 |       13 |     46% |136, 149, 167-179, 182, 219, 224, 259-260, 277-278, 282-290, 326, 330, 332, 334, 336, 341-342, 345-350, 353-354, 357-358, 366-370, 373-388, 393, 398-418, 422-440, 444-480, 483-531, 548-558, 562-608, 612-624, 627-672, 676-682 |
| src/pyefis/instruments/gauges/arc.py                    |      223 |        0 |       66 |        0 |    100% |           |
| src/pyefis/instruments/gauges/egt.py                    |       70 |       60 |       30 |        0 |     10% |28-52, 55-84, 89-96 |
| src/pyefis/instruments/gauges/horizontalBar.py          |      131 |        0 |       34 |        4 |     98% |29-\>31, 72-\>86, 88-\>101, 105-\>118 |
| src/pyefis/instruments/gauges/numeric.py                |       60 |        0 |       10 |        0 |    100% |           |
| src/pyefis/instruments/gauges/stratux\_traffic.py       |       39 |       30 |        4 |        0 |     21% |8-11, 14-18, 21-45 |
| src/pyefis/instruments/gauges/verticalBar.py            |      245 |        0 |       72 |        0 |    100% |           |
| src/pyefis/instruments/helpers/\_\_init\_\_.py          |       40 |        0 |       16 |        0 |    100% |           |
| src/pyefis/instruments/hsi/\_\_init\_\_.py              |      461 |      112 |      102 |       15 |     68% |45-46, 87-95, 101-109, 136, 140, 224-\>228, 228-\>232, 232-\>236, 236-\>241, 278-297, 301, 304-314, 344-347, 350, 353-357, 368-\>exit, 373, 376-379, 382-385, 388-391, 394-397, 403, 406-408, 413-416, 419-422, 425-428, 433, 437, 488-490, 492-494, 496-498, 505, 508-510, 614, 617-619, 628, 632 |
| src/pyefis/instruments/listbox/\_\_init\_\_.py          |      213 |       78 |       58 |        9 |     57% |30-31, 81, 84, 87-88, 91-92, 95-96, 99-100, 103-104, 107-108, 112, 116-120, 123, 126-135, 138, 206-\>208, 222-\>226, 226-\>234, 231, 239, 245, 249, 265, 271-285, 288-315 |
| src/pyefis/instruments/misc/\_\_init\_\_.py             |      167 |        0 |       20 |        0 |    100% |           |
| src/pyefis/instruments/pa/\_\_init\_\_.py               |       70 |       29 |       10 |        1 |     52% |60-72, 75, 79-95, 98 |
| src/pyefis/instruments/tc/\_\_init\_\_.py               |      220 |       42 |       40 |       16 |     75% |36, 42, 60, 77-\>80, 83-\>101, 122, 125-126, 139, 147-148, 157, 159, 168-172, 178, 181-182, 190, 192, 195-199, 217, 220-222, 227, 230-236, 241, 317, 320-322 |
| src/pyefis/instruments/vsi/\_\_init\_\_.py              |      382 |       76 |       68 |       12 |     75% |46, 146-147, 163-172, 189, 192-194, 228, 278-279, 283-286, 289, 292-293, 300, 304, 341-360, 363-374, 404-\>409, 406-\>408, 466, 469, 476-477, 484-491, 495-497, 505-513, 516, 518-520, 524, 526-528, 532, 534-536 |
| src/pyefis/instruments/weston/\_\_init\_\_.py           |       51 |       51 |       10 |        0 |      0% |      1-67 |
| src/pyefis/main.py                                      |      158 |      158 |       64 |        0 |      0% |    18-254 |
| src/pyefis/screens/\_\_init\_\_.py                      |        0 |        0 |        0 |        0 |    100% |           |
| src/pyefis/screens/ems\_sm.py                           |       99 |       99 |       24 |        0 |      0% |    17-341 |
| src/pyefis/screens/epfd.py                              |      104 |      104 |       12 |        0 |      0% |    17-151 |
| src/pyefis/screens/pfd.py                               |      127 |      127 |        2 |        0 |      0% |    17-232 |
| src/pyefis/screens/pfd\_sm.py                           |      108 |      108 |        2 |        0 |      0% |    17-169 |
| src/pyefis/screens/r582\_sm.py                          |       98 |       98 |       24 |        0 |      0% |    17-210 |
| src/pyefis/screens/screenbuilder.py                     |      719 |      719 |      438 |        0 |      0% |    17-978 |
| src/pyefis/screens/sixpack.py                           |       53 |       53 |        2 |        0 |      0% |     17-88 |
| src/pyefis/screens/test.py                              |       21 |       21 |        2 |        0 |      0% |     17-48 |
| src/pyefis/user/\_\_init\_\_.py                         |        0 |        0 |        0 |        0 |    100% |           |
| src/pyefis/user/blake\_pfd/\_\_init\_\_.py              |        0 |        0 |        0 |        0 |    100% |           |
| src/pyefis/user/blake\_pfd/advance\_route.py            |       16 |       16 |        4 |        0 |      0% |      1-25 |
| src/pyefis/user/blake\_pfd/airdata.py                   |      137 |      137 |        8 |        0 |      0% |    15-328 |
| src/pyefis/user/blake\_pfd/airdata\_calculations.py     |       10 |        1 |        2 |        1 |     83% |        10 |
| src/pyefis/user/blake\_pfd/airport\_info\_page.py       |       56 |       56 |        8 |        0 |      0% |      1-98 |
| src/pyefis/user/blake\_pfd/airport\_lookup.py           |       30 |       30 |        8 |        0 |      0% |      1-53 |
| src/pyefis/user/blake\_pfd/config\_loader.py            |      150 |       15 |        8 |        1 |     86% |167-173, 194-197, 200-208, 212 |
| src/pyefis/user/blake\_pfd/create\_route.py             |       18 |       18 |        4 |        0 |      0% |      1-28 |
| src/pyefis/user/blake\_pfd/data/\_\_init\_\_.py         |        2 |        0 |        0 |        0 |    100% |           |
| src/pyefis/user/blake\_pfd/data/csv\_loader.py          |       36 |        7 |        8 |        1 |     73% |18, 26, 51-56 |
| src/pyefis/user/blake\_pfd/database\_importer.py        |      139 |       85 |       28 |        1 |     33% |52-70, 72-75, 78-81, 84-95, 105-127, 130-141, 151, 153, 156, 158-163, 166, 175-192, 201-215, 218-239, 241 |
| src/pyefis/user/blake\_pfd/direct\_to.py                |       36 |       36 |        4 |        0 |      0% |      1-62 |
| src/pyefis/user/blake\_pfd/ems\_page.py                 |      195 |      195 |       78 |        0 |      0% |     1-461 |
| src/pyefis/user/blake\_pfd/engine\_data.py              |       20 |       20 |        0 |        0 |      0% |      1-27 |
| src/pyefis/user/blake\_pfd/engine\_sim.py               |       32 |       32 |        2 |        0 |      0% |      1-78 |
| src/pyefis/user/blake\_pfd/flight\_computer.py          |      104 |       65 |       18 |        0 |     32% |54-63, 66-131, 134-147, 156-176, 180-188, 192-196, 200 |
| src/pyefis/user/blake\_pfd/flight\_logger.py            |       44 |       44 |       18 |        0 |      0% |      1-67 |
| src/pyefis/user/blake\_pfd/fms\_page.py                 |       58 |       58 |       12 |        0 |      0% |      1-96 |
| src/pyefis/user/blake\_pfd/hardware\_readers.py         |      209 |      209 |       18 |        0 |      0% |    19-528 |
| src/pyefis/user/blake\_pfd/log\_replay.py               |       22 |       22 |        2 |        0 |      0% |      1-31 |
| src/pyefis/user/blake\_pfd/log\_viewer.py               |       92 |       92 |       44 |        0 |      0% |     1-136 |
| src/pyefis/user/blake\_pfd/master\_warning.py           |       50 |       50 |       28 |        0 |      0% |      1-81 |
| src/pyefis/user/blake\_pfd/moving\_map.py               |       23 |       23 |        2 |        0 |      0% |      1-54 |
| src/pyefis/user/blake\_pfd/nav\_math.py                 |       67 |       37 |        2 |        0 |     43% |41-80, 98-105, 114-126, 136-152, 160-164, 168, 172, 176 |
| src/pyefis/user/blake\_pfd/navpoint\_database.py        |       30 |       30 |        8 |        0 |      0% |      1-52 |
| src/pyefis/user/blake\_pfd/nearest\_airports.py         |       20 |       20 |        4 |        0 |      0% |      1-41 |
| src/pyefis/user/blake\_pfd/nearest\_page.py             |       32 |       32 |        8 |        0 |      0% |      1-82 |
| src/pyefis/user/blake\_pfd/obstacles.py                 |       22 |       22 |        0 |        0 |      0% |      1-40 |
| src/pyefis/user/blake\_pfd/performance\_calculations.py |       24 |       18 |        0 |        0 |     25% |16-19, 30-31, 47-64, 68 |
| src/pyefis/user/blake\_pfd/pfd\_demo.py                 |      765 |      765 |      176 |        0 |      0% |    1-1204 |
| src/pyefis/user/blake\_pfd/route\_manager.py            |       66 |       44 |       18 |        1 |     27% |24-25, 32-48, 55-61, 64-71, 74-84, 90-103, 105-108, 111-123, 127 |
| src/pyefis/user/blake\_pfd/safe\_taxi.py                |       16 |       16 |        0 |        0 |      0% |      1-23 |
| src/pyefis/user/blake\_pfd/sensors\_sim.py              |       70 |       43 |       14 |        0 |     32% |35-37, 40-85, 105, 109-113 |
| src/pyefis/user/blake\_pfd/set\_cdi\_mode.py            |       22 |       22 |        4 |        0 |      0% |      1-39 |
| src/pyefis/user/blake\_pfd/set\_declutter.py            |       20 |       20 |        4 |        0 |      0% |      1-35 |
| src/pyefis/user/blake\_pfd/set\_fuel\_total.py          |       19 |       19 |        2 |        0 |      0% |      1-34 |
| src/pyefis/user/blake\_pfd/set\_map\_range.py           |       21 |       21 |        4 |        0 |      0% |      1-37 |
| src/pyefis/user/blake\_pfd/set\_obs.py                  |       25 |       25 |        2 |        0 |      0% |      1-40 |
| src/pyefis/user/blake\_pfd/set\_overlay.py              |       42 |       42 |       12 |        0 |      0% |      1-90 |
| src/pyefis/user/blake\_pfd/set\_sim\_control.py         |       23 |       23 |        8 |        0 |      0% |      1-44 |
| src/pyefis/user/blake\_pfd/set\_sim\_profile.py         |       22 |       22 |        4 |        0 |      0% |      1-47 |
| src/pyefis/user/blake\_pfd/set\_vnav.py                 |       27 |       27 |        4 |        0 |      0% |      1-43 |
| src/pyefis/user/blake\_pfd/set\_waypoint.py             |       29 |       29 |        4 |        0 |      0% |      1-48 |
| src/pyefis/user/blake\_pfd/startup\_check.py            |       38 |       38 |        6 |        0 |      0% |      1-59 |
| src/pyefis/user/blake\_pfd/stratux\_reader.py           |       54 |       54 |        4 |        0 |      0% |      1-84 |
| src/pyefis/user/blake\_pfd/synthetic\_vision.py         |       35 |       35 |        2 |        0 |      0% |      1-80 |
| src/pyefis/user/blake\_pfd/terrain.py                   |       20 |       20 |        4 |        0 |      0% |      1-30 |
| src/pyefis/user/blake\_pfd/test\_airdata.py             |        5 |        0 |        0 |        0 |    100% |           |
| src/pyefis/user/blake\_pfd/test\_flight\_computer.py    |       10 |        6 |        2 |        1 |     42% |  6-10, 14 |
| src/pyefis/user/blake\_pfd/weather\_reader.py           |       29 |       29 |        2 |        0 |      0% |      1-52 |
| src/pyefis/user/hooks/\_\_init\_\_.py                   |        0 |        0 |        0 |        0 |    100% |           |
| src/pyefis/user/hooks/composite.py                      |      103 |      103 |       26 |        0 |      0% |    22-165 |
| src/pyefis/user/hooks/keys.py                           |       19 |       19 |        4 |        0 |      0% |     20-53 |
| src/pyefis/user/screens/\_\_init\_\_.py                 |        0 |        0 |        0 |        0 |    100% |           |
| src/pyefis/version.py                                   |        2 |        0 |        0 |        0 |    100% |           |
| **TOTAL**                                               | **10378** | **6019** | **2736** |  **119** | **39%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/gregablake/Blake-pyEfis/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/gregablake/Blake-pyEfis/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/gregablake/Blake-pyEfis/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/gregablake/Blake-pyEfis/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2Fgregablake%2FBlake-pyEfis%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/gregablake/Blake-pyEfis/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.