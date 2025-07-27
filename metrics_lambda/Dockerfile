FROM public.ecr.aws/lambda/python:3.9

# Copy requirements and install dependencies
COPY metrics_lambda/requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install --no-cache-dir -r requirements.txt

# Copy function code
COPY metrics_lambda/lambda_function.py ${LAMBDA_TASK_ROOT}

# Set environment variables
ENV DYNAMODB_TABLE_METRICS=AgentMetrics
ENV CREATE_TABLE_IF_NOT_EXISTS=true

# Set the CMD to your handler
CMD ["lambda_function.lambda_handler"]
