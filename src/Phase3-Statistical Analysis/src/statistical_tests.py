import pandas as pd
from scipy.stats import shapiro, ttest_ind, mannwhitneyu


class StatisticalTester:
    def __init__(self, alpha=0.05):
        self.alpha = alpha

    def groups(self , df , value_column , group_column="period_group"):
        past = df[df[group_column] == "past_period"][value_column]
        recent = df[df[group_column] == "recent_period"][value_column]
        return past, recent


    def shapiro_test(self, data):
        
        statistic, p_value = shapiro(data)

        return {
            "test": "Shapiro-Wilk",
            "statistic": statistic,
            "p_value": p_value,
            "is_normal": p_value >= self.alpha
        }

    def welch_t_test(self, recent, past):
        statistic, p_value = ttest_ind(
            recent,
            past,
            equal_var=False,
            alternative="greater"
        )

        return {
            "test": "Welch independent t-test",
            "alternative": "recent > past",
            "statistic": statistic,
            "p_value": p_value,
            "is_significant": p_value < self.alpha
        }

    def mann_whitney_test(self, recent, past):
        statistic, p_value = mannwhitneyu(
            recent,
            past,
            alternative="greater"
        )

        return {
            "test": "Mann-Whitney U test",
            "alternative": "recent > past",
            "statistic": statistic,
            "p_value": p_value,
            "is_significant": p_value < self.alpha
        }

    def choosing_test(self, past_normality, recent_normality):
        if past_normality["is_normal"] and recent_normality["is_normal"]:
            return "welch"

        return "mannwhitney"

    def run_hypothesis_test(self , df , value_column , hypothesis_name, group_column="period_group" ):
        
        past, recent = self.groups(
            df=df,
            value_column=value_column,
            group_column=group_column
        )
        
        past_normality = self.shapiro_test(past)
        recent_normality = self.shapiro_test(recent)

        selected_test = self.choosing_test(
            past_normality=past_normality,
            recent_normality=recent_normality
        )

        if selected_test == "welch":
            test_result = self.welch_t_test(recent, past)
        else:
            test_result = self.mann_whitney_test(recent, past)

        result = {
            "hypothesis_name": hypothesis_name,
            "value_column": value_column,
            "alpha": self.alpha,

            "past_sample_size": len(past),
            "recent_sample_size": len(recent),

            "past_mean": past.mean(),
            "recent_mean": recent.mean(),
            "mean_difference": recent.mean() - past.mean(),

            "past_normality": past_normality,
            "recent_normality": recent_normality,

            "selected_test": selected_test,
            "test_result": test_result,

            "description": self.describe_result(test_result)
        }

        return result

    def describe_result(self, test_result):
        p_value = test_result["p_value"]

        if p_value < self.alpha:
            return (
            f"از آنجا که مقدار p-value برابر با {p_value:.4f} است و از سطح معناداری alpha = {self.alpha} کمتر می‌باشد، فرض صفر رد می‌شود.\n"
            "بنابراین شواهد آماری معناداری وجود دارد که نشان می‌دهد مقدار متغیر مورد بررسی در دوره اخیر بیشتر از دوره گذشته است."
        )

        return (
          f"از آنجا که مقدار p-value برابر با {p_value:.4f} است و از سطح معناداری alpha = {self.alpha} بزرگ‌تر یا مساوی می‌باشد، فرض صفر رد نمی‌شود.\n"
          "بنابراین شواهد آماری کافی وجود ندارد که نتیجه بگیریم مقدار متغیر مورد بررسی در دوره اخیر بیشتر از دوره گذشته است."
        )

    def print_report(self, result):
            print("=" * 80)
            print(f"Hypothesis Test Report: {result['hypothesis_name']}")
            print("=" * 80)

            print("\nValue Column:")
            print(result["value_column"])

            print("\nSample Sizes:")
            print("Past period:", result["past_sample_size"])
            print("Recent period:", result["recent_sample_size"])

            print("\nMeans:")
            print("Past mean:", result["past_mean"])
            print("Recent mean:", result["recent_mean"])
            print("Mean difference:", result["mean_difference"])

            print("\nNormality Test - Past Period:")
            print(result["past_normality"])

            print("\nNormality Test - Recent Period:")
            print(result["recent_normality"])

            print("\nSelected Test:")
            print(result["selected_test"])

            print("\nTest Result:")
            print(result["test_result"])

            print("\nDescription:")
            print(result["description"])

            print("=" * 80)