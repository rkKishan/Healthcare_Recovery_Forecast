"""
The assistant: a tool-calling chat layer over the same services the REST API
and the PDF reports already use.

The model never computes anything. It chooses which of the application's own
functions to call, and puts the result into a sentence. Every number it says
came out of the trained XGBoost model, the SHAP explainer, or the prediction
log -- which is the only way a chat surface can sit on top of a clinical
forecast without becoming a second, unvalidated source of predictions.
"""
