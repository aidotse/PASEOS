import asyncio
import pykep as pk
import torch
import time
import paseos
from paseos import ActorBuilder, SpacecraftActor
from simple_neural_network import SimpleNeuralNetwork

class Node:
    """Class that encapsulates a PASEOS instance and a neural network to perform binary classification. 
    Three activites are included: communicate, train, and stand by
    """    
    def __init__(self, node_id,  pos_and_vel, paseos_cfg, power_consumption_in_watt):
        
        # Create PASEOS instance to node
        earth = pk.planet.jpl_lp("earth")
        self.node_id = node_id
        sat = ActorBuilder.get_actor_scaffold(f"sat{node_id}", SpacecraftActor, pk.epoch(0))
        ActorBuilder.set_orbit(sat, pos_and_vel[0], pos_and_vel[1], pk.epoch(0), earth)
        ActorBuilder.set_power_devices(sat, 8000, 10000, 1)
        ActorBuilder.add_comm_device(sat, device_name="link", bandwidth_in_kbps=1000)
        self.paseos = paseos.init_sim(sat, paseos_cfg)
        
        # Create a simple neural network
        self.model = SimpleNeuralNetwork(node_id)
        self.model.set_optimizer(torch.optim.SGD(self.model.parameters(), lr=0.1))
        self.model.set_loss_fn(torch.nn.BCELoss())
        
        transmit_bits = self.model_size()
        self.transmit_duration = transmit_bits / (1000*self.paseos.local_actor.communication_devices['link'].bandwidth_in_kbps)
        
        self.training_time = None
        
        #constraint_function = lambda x: self.paseos._operations_monitor.
        self.paseos.register_activity("Train", 
                                      activity_function=self.train, 
                                      power_consumption_in_watt=power_consumption_in_watt,
                                      constraint_function=None)
        
        self.paseos.register_activity("Communicate", 
                                      activity_function=self.communicate_model, 
                                      power_consumption_in_watt=power_consumption_in_watt,
                                      constraint_function=None)
        
        self.paseos.register_activity("StandBy", 
                                      activity_function=self.stand_by, 
                                      power_consumption_in_watt=0,
                                      constraint_function=None)
    
    def model_size(self):
        """Get the size of the model parameters in bits

        """        
        # Return model parameters as a list of NumPy ndarrays
        bytestream = b""  # Empty byte represenation
        for _, val in self.model.state_dict().items():  # go over each layer
            bytestream += val.cpu().numpy().tobytes()  # convert layer to bytes and concatenate
        return len(bytestream)*8
    
    def local_time(self):
        """Get the local epoch

        """        
        return self.paseos.local_actor.local_time
    
    def add_known_node(self, node):
        """Add the actor of a node to the list of known actors

        """        
        self.paseos.add_known_actor(node.paseos.local_actor)
    
    def activity_scheduler(self):
        """Determine what activity should be performed"""
        if self.paseos.local_actor.state_of_charge > 0.2:
            return "train"
        else:
            return "standby"
        
    def in_in_line_of_sight(self, target_node):
        """Check if node is in line of sight

        Args:
            target_node (Node): other node in simulation

        Returns:
            bool: True if nodes are in line of sight
        """        
        target_actor = target_node.paseos.local_actor
        local_actor = self.paseos.local_actor
        return local_actor.is_in_line_of_sight(target_actor, self.local_time())
    
    def transmission_is_feasible(self, target_node):
        """Check if there will be line-of-sight in end of transmission

        Args:
            target_node (Node): other node in simulation

        Returns:
            bool: True if there will be line-of-sight at the end of transmission
        """        
        target_actor = target_node.paseos.local_actor
        local_actor = self.paseos.local_actor
        
        transmit_end = pk.epoch(self.local_time().mjd2000 + self.transmit_duration*pk.SEC2DAY)
        los_end = local_actor.is_in_line_of_sight(target_actor, transmit_end)
        return los_end
    
    def merge_model(self, received_model):
        """Aggregate received model with local via averaging

        Args:
            received_model (_type_): Received model parameters
        """        
        local_sd = self.model.state_dict()
        received_sd = received_model.state_dict()
        for key in local_sd:
            local_sd[key] = 0.5 * local_sd[key] + 0.5*received_sd[key]
        self.model.load_state_dict(local_sd)
    
    async def train(self, args):
        """Training activity

        Args:
            args (_type_): List of previous accuracies
        """        
        start_time = time.time()
        self.model.train()
        acc = self.model.eval()
        args.append(acc)
        self.training_time = time.time() - start_time
    
    async def communicate_model(self, args):
        """Emulate communication by sleeping for transmission duration

        """        
        await asyncio.sleep(self.transmit_duration)
    
    async def stand_by(self, args):
        """Stand by activity, do nothing

        Args:
            args (_type_): list of previous accuracies
        """        
        args.append(args[-1])
        await asyncio.sleep(self.training_time)
        