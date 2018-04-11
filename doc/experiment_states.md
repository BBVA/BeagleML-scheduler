# Experiment states

The scheduler controls experiments lifecycle by assigning to each experiment the following states:
- ***Queue*** : State by default when an project definition is loaded.

- ***Pool*** : State reached when the user clicks "play button" in the automodeling-front. The experiment goes from "queue" to "pool".

- ***Completed*** : State reached when the experiment has processed all the data, and has finished the training process.

 This is the only state where ***the experiment informs*** that it has finished, by sending a message to the correspondent Kafka topic.

- ***Timeout*** : State reached when the experiment ends, because it hasn't finished processing data within the given period of time.

- ***Accuracy Limit Reached*** : State reached when the experiment ends, because it has already reached the expected accuracy.
So it is not necessary to continue its execution anymore.

- ***Stopped*** : State reached when the user clicks the "pause button" in the automodeling-front. The experiment goes from "pool" to "stopped".

- ***Failed*** : State reached when the experiment can not continue due to Kafka error. The experiment goes from "pool" to "failed".
