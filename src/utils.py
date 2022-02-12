# Copyright (c) Meta Platforms, Inc. and affiliates.
# This source code is licensed under the CC-BY-NC license found in the
# LICENSE file in the root directory of this source tree.

# Function that calculates pareto frontier given a set of points
def pareto_frontier(Xs, Ys, maxX=True, maxY= True):
    # Sort the list in descending order of X
    tmp_list = sorted([[Xs[i], Ys[i]] for i in range(len(Xs))], reverse=maxX)
    # Start with the first value in the sorted list
    front_point = [tmp_list[0]]    
    for pair in tmp_list[1:]:
        if maxY is True: 
            if pair[1] >= front_point[-1][1]:
                front_point.append(pair)
        else:
            if pair[1] <= front_point[-1][1]:
                front_point.append(pair)
    frontX = [pair[0] for pair in front_point]
    frontY = [pair[1] for pair in front_point]
    return frontX, frontY

