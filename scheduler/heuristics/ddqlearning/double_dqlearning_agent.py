"""
Copyright 2018 Banco Bilbao Vizcaya Argentaria, S.A.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from collections import deque
import numpy as np
import random
import abc


class DoubleDQLearningAgent:
    def __init__(self, state_size, action_size):
        self.state_size = state_size
        self.action_size = action_size

        # hyperparameters
        self.gamma = 0.95  # discount rate on future rewards
        self.epsilon = 1.0  # exploration rate
        self.epsilon_decay = 0.995  # the decay of epsilon after each training batch
        self.epsilon_min = 0.1  # the minimum exploration rate permissible
        self.batch_size = 32  # maximum size of the batches sampled from memory

        # agent state
        self.model = self.build_model()
        self.model_t = self.build_model()
        self.memory = deque(maxlen=2000)

    @abc.abstractmethod
    def build_model(self):
        return None

    def select_action(self, state, do_train=True):
        if do_train and np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)
        return np.argmax(self.model_t.predict(state)[0])

    def record(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def replay(self):
        if len(self.memory) < self.batch_size:
            return 0

        minibatch = random.sample(self.memory, self.batch_size)
        for state, action, reward, next_state, done in minibatch:
            target = reward
            if not done:
                target = (reward + self.gamma *
                          np.amax(self.model.predict(next_state)[0]))
            target_f = self.model.predict(state)
            target_f[0][action] = target
            self.model.fit(state, target_f, epochs=1, verbose=0)

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def update_target(self):
        weights = self.model.get_weights()
        self.model_t.set_weights(weights)
        self.save()
        pass

    def save(self):
        self.model.save_weights('/tmp/weights.h5', overwrite=True)
        pass
