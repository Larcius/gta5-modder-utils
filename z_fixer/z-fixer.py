# TODO refactoring needed
import os
import getopt
import random
import re
import shutil
import struct
import sys
from typing import Optional

import transforms3d
from dataclasses import dataclass
from natsort import natsorted


@dataclass
class Tree:
    trunkRadius: float
    offsetZ: float = 0
    maxOffsetZ: Optional[float] = None

    def getRandomOffsetZ(self) -> float:
        maxOffsetZ = self.offsetZ if (DISABLE_INCREASE_OF_Z or self.maxOffsetZ is None or self.maxOffsetZ > self.offsetZ) else self.maxOffsetZ
        return random.uniform(maxOffsetZ, self.offsetZ)


# if True then z coordinate will not be changed if calculated value is greater than original value
DISABLE_INCREASE_OF_Z = False

IGNORE_BUSHES = True

DELETE_IF_ON_STREET = False


# trees can be found at x64i.rpf\levels\gta5\props\vegetation\v_trees.rpf\
# and update\x64\dlcpacks\patchday2ng\dlc.rpf\x64\levels\gta5\props\vegetation\v_trees.rpf

trees = {
    # trees
    "prop_rio_del_01": Tree(1, 0.09),
    "prop_rus_olive": Tree(0.55, 0.08),
    "prop_s_pine_dead_01": Tree(0.55),
    "prop_tree_birch_01": Tree(0.95, -0.01),
    "prop_tree_birch_02": Tree(0.63),
    "prop_tree_birch_03": Tree(0.24, -0.03),
    "prop_tree_birch_03b": Tree(0.18, -0.04),
    "prop_tree_birch_04": Tree(0.57, -0.03),
    "prop_tree_birch_05": Tree(0.22, -0.06),
    "prop_tree_cedar_02": Tree(1.4, 0.08),
    "prop_tree_cedar_03": Tree(1.4, 0.08),
    "prop_tree_cedar_04": Tree(1.4, 0.09),
    "prop_tree_cedar_s_01": Tree(0.52, 0.03),
    "prop_tree_cedar_s_02": Tree(0.13, 0.01),
    "prop_tree_cedar_s_04": Tree(1),
    "prop_tree_cedar_s_05": Tree(0.7),
    "prop_tree_cedar_s_06": Tree(0.6),
    "prop_tree_cypress_01": Tree(0.7),
    "prop_tree_eng_oak_01": Tree(1.13, -0.02),
    "prop_tree_eucalip_01": Tree(1.51, -0.17),
    "prop_tree_fallen_pine_01": Tree(1.25, 0.54, 0.2),
    "prop_tree_jacada_01": Tree(0.56, -0.06),
    "prop_tree_jacada_02": Tree(0.71, 0.1),
    "prop_tree_lficus_02": Tree(1, 0.39, 0),
    "prop_tree_lficus_03": Tree(0.85, -0.02, -0.21),
    "prop_tree_lficus_05": Tree(1.45, 0.08, -0.09),
    "prop_tree_lficus_06": Tree(1.9, 0.10, -0.15),
    "prop_tree_maple_02": Tree(0.41, 0.05),
    "prop_tree_maple_03": Tree(0.35, 0.05),
    "prop_tree_mquite_01": Tree(0.45, -0.03),
    "prop_tree_oak_01": Tree(2.68, -0.07),
    "prop_tree_olive_01": Tree(1.6, 0.1),
    "prop_tree_pine_01": Tree(0.82, 0.44),
    "prop_tree_pine_02": Tree(0.80, -0.04),
    "prop_tree_stump_01": Tree(0.70, 0.02),
    "prop_w_r_cedar_01": Tree(1.34, 0.09),
    "prop_w_r_cedar_dead": Tree(1.34, 0.09),
    "test_tree_cedar_trunk_001": Tree(1.3, 0.09),
    "test_tree_forest_trunk_01": Tree(4.82, -0.03),
    "test_tree_forest_trunk_base_01": Tree(4.25),
    # bushes
    "prop_bush_lrg_02": Tree(3, 0.188, 0),
    "prop_bush_lrg_02b": Tree(1.1, -0.01),
    "prop_bush_lrg_04b": Tree(2.6, 2.2, 0),
    "prop_bush_lrg_04c": Tree(2.6, 2.2, 0),
    "prop_bush_lrg_04d": Tree(2.6, 2.2, 0),
    # palms
    "prop_palm_sm_01a": Tree(0.65, -0.05, -0.5),
    "prop_palm_sm_01d": Tree(0.7, -0.05, -0.57),
    "prop_palm_sm_01e": Tree(1.1, -0.05, -1.75),
    "prop_palm_sm_01f": Tree(0.72, 0, -1.15),
    "prop_palm_med_01a": Tree(0.89, 0, -0.87),
    "prop_palm_med_01b": Tree(1, -0.05, -1.3),
    "prop_palm_med_01c": Tree(1.2, -0.1, -1.5),
    "prop_palm_med_01d": Tree(1.15, 0, -0.9),
    "prop_fan_palm_01a": Tree(1.2, 0.23, -1),
    "prop_palm_fan_02_a": Tree(0.6, -0.05, -0.8),
    "prop_palm_fan_02_b": Tree(1.35, -0.1, -1.28),
    "prop_palm_fan_04_a": Tree(0.65, -0.1, -0.7),
    "prop_palm_fan_04_b": Tree(0.85, -0.12, -0.8),
    "prop_palm_fan_03_a": Tree(1.7, -0.03, -1.5),
    "prop_palm_fan_03_b": Tree(0.9, -0.03, -1.6),
    "prop_palm_fan_03_c": Tree(1, 0, -1.9),
    "prop_palm_fan_03_c_graff": Tree(1, 0, -1.9),
    "prop_palm_fan_03_d": Tree(0.8, 0, -1.7),
    "prop_palm_fan_03_d_graff": Tree(0.8, 0, -1.7),
    "prop_palm_fan_04_c": Tree(1.25, -0.22, -1.1),
    "prop_palm_fan_04_d": Tree(1.5, -0.15, -1.1),
    "prop_palm_huge_01a": Tree(0.95, 0.37, -0.25),
    "prop_palm_huge_01b": Tree(0.95, -0.08, -1.2),
}


def main(argv):
    # True means extract x, y coordinates
    # False means fix z coordinates
    enableModeExtract = True

    usageMsg = "z-fixer.py [--extract|--fix]"

    try:
        opts, args = getopt.getopt(argv, "h?e:f:", ["help", "extract", "fix"])
    except getopt.GetoptError:
        print("ERROR: Unknown argument. Please see below for usage.")
        print(usageMsg)
        sys.exit(2)

    if len(opts) == 0:
        print("ERROR: Neither --extract nor --fix argument was given. Please see below for usage.")
        print(usageMsg)
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-h', '-?', '--help'):
            print(usageMsg)
            sys.exit(0)
        elif opt in ("-e", "--extract"):
            enableModeExtract = True
        elif opt in ("-f", "--fix"):
            enableModeExtract = False

    generatedDir = os.path.join(os.path.dirname(__file__), "generated")
    if os.path.exists(generatedDir):
        shutil.rmtree(generatedDir)
    os.mkdir(generatedDir)

    outCoords = heightmap = None
    if enableModeExtract:
        outCoords = open(os.path.join(generatedDir, "coords.txt"), 'w')
    else:
        heightmap = open(os.path.join(os.path.dirname(__file__), 'heights', 'hmap.txt'), 'r')

    # create high quality files
    for filename in natsorted(os.listdir(os.path.join(os.path.dirname(__file__), "maps"))):
        if not filename.endswith(".ymap.xml") or filename.endswith("_lod.ymap.xml"):
            continue

        f = open(os.path.join(os.path.dirname(__file__), "maps", filename), 'r')
        content = f.read()
        f.close()

        content_new = re.sub('(<Item type="CEntityDef">' +
                             '\\s*<archetypeName>([^<]+)</archetypeName>' +
                             '(?:\\s*<[^/].*>)*?' +
                             '\\s*<position x="([^>]+)" y="([^>]+)" z=")([^"]+)("\\s*/>' +
                             '\\s*<rotation x="([^>]+)" y="([^>]+)" z="([^"]+)" w="([^"]+)"\\s*/>' +
                             '(?:\\s*<[^/].*>)*?' +
                             '\\s*<scaleXY\\s+value="([^"]+)"\\s*/>' +
                             '\\s*<scaleZ\\s+value="([^"]+)"\\s*/>' +
                             '(?:\\s*<[^/].*>)*?' +
                             '\\s*</Item>\\s*)', lambda match: repl(match, outCoords, heightmap), content, flags=re.M)

        if not enableModeExtract:
            f = open(os.path.join(os.path.dirname(__file__), "generated", filename), 'w')
            f.write(content_new)
            f.close()

    if heightmap is not None:
        heightmap.close()


def getMinHeight(heightmap) -> [float, float]:
    heightmapEntry = heightmap.readline().rstrip("\n")
    if not heightmapEntry:
        print("ERROR: cannot get entry in heightmap")
        quit()

    parts = heightmapEntry.split(",")

    if len(parts) < 5:
        print("ERROR: invalid line in heightmap entry:")
        print(heightmapEntry)
        quit()

    return float(parts[3]), float(parts[4])


def floatToStr(val):
    return "{:.8f}".format(val)


def hashFloat(val: float) -> int:
    return hash(struct.pack("f", val))


def repl(matchobj, outCoords, heightmap):
    global trees

    prop = matchobj.group(2).lower()

    if prop not in trees or (IGNORE_BUSHES and prop.startswith("prop_bush_")):
        return matchobj.group(0)

    tree = trees[prop]

    coords = [float(matchobj.group(3)), float(matchobj.group(4)), float(matchobj.group(5))]
    scaleXY = float(matchobj.group(11))
    scaleZ = float(matchobj.group(12))
    origQuat = [float(matchobj.group(10)), -float(matchobj.group(7)), -float(matchobj.group(8)), -float(matchobj.group(9))]  # order is w, -x, -y, -z

    # set a seed here to get the same offsetZ for multiple runs
    seed = hashFloat(coords[0]) ^ hashFloat(coords[1])
    random.seed(a=seed)
    offsetZ = tree.getRandomOffsetZ()

    transformed = transforms3d.quaternions.rotate_vector([0, 0, -offsetZ * scaleZ], origQuat)

    if outCoords is not None:
        for i in range(3):
            coords[i] += transformed[i]

        outCoords.write(str(coords[0]) + "," + str(coords[1]) + "," + str(coords[2]) +
                        "," + str(origQuat[1]) + "," + str(origQuat[2]) + "," + str(origQuat[3]) + "," + str(origQuat[0]) +
                        "," + str(tree.trunkRadius * scaleXY) + "\n")
        return matchobj.group(0)

    minHeight, distanceToStreet = getMinHeight(heightmap)

    calcZCoord = minHeight - transformed[2]

    if DISABLE_INCREASE_OF_Z and calcZCoord > coords[2]:
        calcZCoord = coords[2]

    position = [float(matchobj.group(3)), float(matchobj.group(4)), float(matchobj.group(5))]

    if abs(calcZCoord - coords[2]) > 1:
        print("WARNING: changed Z coordinate of entity", prop, "at position", position, "by", calcZCoord - coords[2],
              "(new z coordinate is " + str(calcZCoord) + ")")

    if DELETE_IF_ON_STREET and distanceToStreet < 3 + tree.trunkRadius * scaleXY:
        print("INFO: removing", prop, "at position", position, "because it is placed on a street or path")
        return ""

    return matchobj.group(1) + floatToStr(calcZCoord) + matchobj.group(6)


if __name__ == "__main__":
    main(sys.argv[1:])
