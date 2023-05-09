from matplotlib import pyplot as plt
import numpy as np

relevance_num_original = [0, 0, 0, 0, 0,
                          0, 0, 0, 0, 1,
                          0, 0, 0, 0, 0,
                          0, 0, 0, 0, 0]
relevance_num_original = np.cumsum(relevance_num_original)

relevance_num_profile_boosting = [1, 1, 1, 0, 0,
                                  0, 0, 0, 0, 0,
                                  0, 0, 1, 0, 0,
                                  0, 0, 0, 0, 0]
relevance_num_profile_boosting = np.cumsum(relevance_num_profile_boosting)

total_num = range(1, 21)
precision_original = [relevance_num_original[i] / total_num[i] for i in range(len(total_num))]
recall_original = [relevance_num_original[i] / 100 for i in range(len(total_num))]

precision_profile_boosting = [relevance_num_profile_boosting[i] / total_num[i] for i in range(len(total_num))]
recall_profile_boosting = [relevance_num_profile_boosting[i] / 100 for i in range(len(total_num))]

plt.plot(precision_original, recall_original, label='Original')
plt.plot(precision_profile_boosting, recall_original, label='Profile boosting')
plt.title("click boosting precision-recall (sports)")
plt.xlabel("precision")
plt.ylabel("recall")
plt.legend()
plt.savefig("./result/profile_boosting_precision_recall_sports.png")
plt.show()
'''
plt.plot(total_num, precision_original, label='Original')
plt.plot(total_num, precision_profile_boosting, label='Profile boosting')
plt.title("click boosting precision (sports)")
plt.xlabel("file count")
plt.ylabel("precision")
plt.legend()
plt.savefig("./result/profile_boosting_precision_sports.png")
plt.show()

plt.plot(total_num, recall_original, label='Original')
plt.plot(total_num, recall_profile_boosting, label='Profile boosting')
plt.title("click boosting recall (sports)")
plt.xlabel("file count")
plt.ylabel("recall")
plt.legend()
plt.savefig("./result/profile_boosting_recall_sports.png")
plt.show()
'''