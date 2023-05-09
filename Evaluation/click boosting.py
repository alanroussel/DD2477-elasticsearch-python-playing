from matplotlib import pyplot as plt
import numpy as np


def click_boosting(relevance_num_original, relevance_num_click_boosting, figure_name):
    relevance_num_original = np.cumsum(relevance_num_original)
    relevance_num_click_boosting = np.cumsum(relevance_num_click_boosting)

    total_num = range(1, 21)
    precision_original = [relevance_num_original[i] / total_num[i] for i in range(len(total_num))]
    recall_original = [relevance_num_original[i] / 100 for i in range(len(total_num))]

    precision_click_boosting = [relevance_num_click_boosting[i] / total_num[i] for i in range(len(total_num))]
    recall_click_boosting = [relevance_num_click_boosting[i] / 100 for i in range(len(total_num))]
    '''
    plt.plot(precision_original, recall_original, label='Original')
    plt.plot(precision_click_boosting, recall_original, label='Click boosting')
    plt.title("click boosting precision-recall ("+figure_name+")")
    plt.xlabel("precision")
    plt.ylabel("recall")
    plt.legend()
    plt.savefig("./result/click_boosting_precision_recall_" + figure_name + ".png")
    plt.show()
    '''
    plt.plot(total_num, precision_original, label='Original')
    plt.plot(total_num, precision_click_boosting, label='Click boosting')
    plt.title("click boosting precision ("+figure_name+")")
    plt.xlabel("file count")
    plt.ylabel("precision")
    plt.legend()
    plt.savefig("./result/click_boosting_precision_" + figure_name + ".png")
    plt.show()
    '''
    plt.plot(total_num, recall_original, label='Original')
    plt.plot(total_num, recall_click_boosting, label='Click boosting')
    plt.title("click boosting recall (" + figure_name + ")")
    plt.xlabel("file count")
    plt.ylabel("recall")
    plt.legend()
    plt.savefig("./result/click_boosting_recall_" + figure_name + ".png")
    plt.show()
    '''

relevance_num_original_sports = [1, 1, 1, 0, 1,
                                 1, 0, 1, 0, 1,
                                 1, 1, 0, 1, 1,
                                 1, 1, 0, 1, 1]
relevance_num_click_boosting_sports = [1, 1, 1, 1, 1,
                                       1, 1, 1, 1, 1,
                                       1, 1, 1, 1, 1,
                                       0, 0, 0, 0, 0]

relevance_num_original_fishing_gear_shops = [1, 0, 1, 1, 1,
                                             0, 0, 0, 0, 0,
                                             0, 0, 0, 0, 0,
                                             0, 0, 0, 0, 0]
relevance_num_click_boosting_fishing_gear_shops = [1, 1, 1, 1, 0,
                                                   0, 0, 0, 0, 0,
                                                   0, 0, 0, 0, 0,
                                                   0, 0, 0, 0, 0]

relevance_num_original_zombie_attack = [1, 1, 1, 1, 1,
                                        0, 1, 1, 1, 1,
                                        0, 1, 1, 1, 0,
                                        0, 0, 1, 0, 0]
relevance_num_click_boosting_zombie_attack = [1, 1, 1, 1, 1,
                                              1, 1, 0, 1, 1,
                                              1, 1, 1, 0, 1,
                                              0, 0, 0, 0, 0]

relevance_num_original_amusement_parks = [0, 0, 0, 1, 1,
                                          0, 0, 1, 0, 1,
                                          1, 0, 0, 0, 1,
                                          0, 1, 1, 1, 0]
relevance_num_click_boosting_amusement_parks = [0, 1, 1, 1, 1,
                                                1, 0, 1, 1, 1,
                                                1, 0, 0, 0, 0,
                                                0, 0, 0, 0, 0]

click_boosting(relevance_num_original_sports, relevance_num_click_boosting_sports, "sports")
click_boosting(relevance_num_original_fishing_gear_shops, relevance_num_click_boosting_fishing_gear_shops,
               "fishing_gear_shops")
click_boosting(relevance_num_original_amusement_parks, relevance_num_click_boosting_amusement_parks, "amusement_parks")
click_boosting(relevance_num_original_zombie_attack, relevance_num_click_boosting_zombie_attack, "zombie_attack")
