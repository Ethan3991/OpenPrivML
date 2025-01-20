# import torch.nn as nn
# import torch
# import torch.nn.functional as F
# import torchvision
# import os
# import config as cfg
# from transfer_learning_clean_imagenet10_0721 import Imagenet10ResNet18

# models_path = cfg.models_path  # Path to save trained models
# adv_img_path = cfg.adv_img_path  # Path to save adversarial images

# # Custom weights initialization function for the generator and discriminator
# def weights_init(m):
#     classname = m.__class__.__name__
#     if classname.find('Conv') != -1:  # If the module is a Convolutional layer
#         nn.init.normal_(m.weight.data, 0.0, 0.02)  # Initialize weights with a normal distribution
#     elif classname.find('BatchNorm') != -1:  # If the module is a BatchNorm layer
#         nn.init.normal_(m.weight.data, 1.0, 0.02)  # Initialize weights with a normal distribution
#         nn.init.constant_(m.bias.data, 0)  # Initialize biases to zero

# # Adversarial Image Generator class
# class Adv_Gen:
#     def __init__(self,
#                  device,
#                  model_extractor,
#                  generator,):
#         """
#         Initialize the Adversarial Image Generator.

#         Args:
#             device (torch.device): The device (CPU/GPU) to run the model on.
#             model_extractor (nn.Module): Feature extractor model.
#             generator (nn.Module): Generator model to create adversarial images.
#         """
#         self.device = device
#         self.model_extractor = model_extractor  # Feature extractor model
#         self.generator = generator  # Generator model

#         self.box_min = cfg.BOX_MIN  # Minimum value for pixel normalization
#         self.box_max = cfg.BOX_MAX  # Maximum value for pixel normalization
#         self.ite = 0  # Iteration counter

#         # Move models to the specified device
#         self.model_extractor.to(device)
#         self.generator.to(device)

#         # Load the classifier model (ResNet-18 trained on ImageNet-10)
#         self.classifer = Imagenet10ResNet18()
#         self.classifer.load_state_dict(torch.load('models/resnet18_imagenet10_transferlearning.pth'))
#         self.classifer.to(device)
#         self.classifer = torch.nn.DataParallel(self.classifer, device_ids=[0, 1])  # Use DataParallel for multi-GPU training

#         # Freeze the classifier's weights while keeping BatchNorm layers unfixed
#         self.classifer.train()  # Set the model to training mode
#         for p in self.classifer.parameters():
#             p.requires_grad = False  # Freeze all layers except BatchNorm

#         # Initialize the optimizer for the generator
#         self.optimizer_G = torch.optim.Adam(self.generator.parameters(), lr=0.001)

#         # Create directories for saving models and adversarial images if they don't exist
#         if not os.path.exists(models_path):
#             os.makedirs(models_path)
#         if not os.path.exists(adv_img_path):
#             os.makedirs(adv_img_path)

#     def train_batch(self, x):
#         """
#         Train the generator for a single batch of images.

#         Args:
#             x (torch.Tensor): Batch of clean images.

#         Returns:
#             loss_adv (float): Adversarial loss value.
#             adv_imgs (torch.Tensor): Generated adversarial images.
#             class_out (torch.Tensor): Classifier output for adversarial images.
#         """
#         self.optimizer_G.zero_grad()  # Clear gradients

#         adv_imgs = self.generator(x)  # Generate adversarial images

#         with torch.no_grad():
#             class_out = self.classifer(adv_imgs)  # Classifier output for adversarial images
#             tagged_feature = self.model_extractor(x)  # Extract features from clean images

#         adv_img_feature = self.model_extractor(adv_imgs)  # Extract features from adversarial images

#         # Compute adversarial loss using L1 loss between features
#         loss_adv = F.l1_loss(tagged_feature, adv_img_feature * cfg.noise_coeff)
#         loss_adv.backward(retain_graph=True)  # Backpropagate gradients

#         self.optimizer_G.step()  # Update generator weights

#         return loss_adv.item(), adv_imgs, class_out

#     def train(self, train_dataloader, epochs):
#         """
#         Train the generator for multiple epochs.

#         Args:
#             train_dataloader (torch.utils.data.DataLoader): DataLoader for training data.
#             epochs (int): Number of epochs to train.
#         """
#         for epoch in range(1, epochs + 1):
#             if epoch == 200:  # Adjust learning rate at epoch 200
#                 self.optimizer_G = torch.optim.Adam(self.generator.parameters(), lr=0.0001)
#             if epoch == 400:  # Adjust learning rate at epoch 400
#                 self.optimizer_G = torch.optim.Adam(self.generator.parameters(), lr=0.00001)

#             loss_adv_sum = 0  # Sum of adversarial losses
#             self.ite = epoch  # Update iteration counter
#             correct = 0  # Counter for correctly classified images
#             total = 0  # Total number of images

#             for i, data in enumerate(train_dataloader, start=0):
#                 images, labels = data  # Extract images and labels from the batch
#                 images, labels = images.to(self.device), labels.to(self.device)

#                 loss_adv_batch, adv_img, class_out = self.train_batch(images)  # Train on the current batch
#                 loss_adv_sum += loss_adv_batch

#                 # Compute classification accuracy
#                 predicted_classes = torch.max(class_out, 1)[1]
#                 correct += (predicted_classes == labels).sum().item()
#                 total += labels.size(0)

#             # Save and visualize adversarial images
#             torchvision.utils.save_image(torch.cat((adv_img[:7], images[:7])),
#                                          adv_img_path + str(epoch) + ".png",
#                                          normalize=True, scale_each=True, nrow=7)

#             # Print training statistics
#             num_batch = len(train_dataloader)
#             print("epoch %d:\n loss_adv: %.3f, \n" %
#                   (epoch, loss_adv_sum / num_batch))
#             print(f"Classification ACC: {correct / total}")

#             # Save the generator model periodically
#             if epoch % 20 == 0:
#                 netG_file_name = models_path + 'netG_epoch_' + str(epoch) + '.pth'
#                 torch.save(self.generator.state_dict(), netG_file_name)

#                 # Save a demo of poisoned samples
#                 trigger_img = torch.squeeze(torch.load('data/tag.pth'))
#                 noised_trigger_img = self.generator(torch.unsqueeze(trigger_img, 0))
#                 torchvision.utils.save_image((images + noised_trigger_img)[:5], 'data/poisoned_sample_demo.png', normalize=True,
#                                              scale_each=True, nrow=5)

import torch.nn as nn
import torch
import torch.nn.functional as F
import torchvision
import os
import config as cfg
from transfer_learning_clean_imagenet10_0721 import Imagenet10ResNet18

# Define paths for saving models and adversarial images
models_path = cfg.models_path
adv_img_path = cfg.adv_img_path

def weights_init(m):
    """Initialize network weights using specific distributions.
    
    Args:
        m (nn.Module): Neural network module to initialize
        
    This function applies custom initialization:
    - Convolutional layers: Normal distribution with mean=0.0, std=0.02
    - BatchNorm layers: Weights from N(1.0, 0.02), biases=0
    """
    classname = m.__class__.__name__
    if classname.find('Conv') != -1:
        nn.init.normal_(m.weight.data, 0.0, 0.02)
    elif classname.find('BatchNorm') != -1:
        nn.init.normal_(m.weight.data, 1.0, 0.02)
        nn.init.constant_(m.bias.data, 0)

class Adv_Gen:
    """Adversarial Generator class for creating adversarial images.
    
    This class implements an adversarial generator that creates perturbed images
    designed to fool a target classifier while maintaining visual similarity
    to original images.
    """
    
    def __init__(self, device, model_extractor, generator):
        """Initialize the adversarial generator.
        
        Args:
            device (torch.device): Device to run computations on (CPU/GPU)
            model_extractor (nn.Module): Model for extracting image features
            generator (nn.Module): Generator network for creating adversarial perturbations
        """
        # Basic setup
        self.device = device
        self.model_extractor = model_extractor
        self.generator = generator
        
        # Set pixel value bounds for normalization
        self.box_min = cfg.BOX_MIN
        self.box_max = cfg.BOX_MAX
        self.ite = 0  # Iteration counter
        
        # Move models to specified device
        self.model_extractor.to(device)
        self.generator.to(device)
        
        # Setup classifier (ResNet18 pretrained on ImageNet10)
        self.classifer = Imagenet10ResNet18()
        self.classifer.load_state_dict(torch.load('models/resnet18_imagenet10_transferlearning.pth'))
        self.classifer.to(device)
        # Enable multi-GPU training for classifier
        self.classifer = torch.nn.DataParallel(self.classifer, device_ids=[0, 1])
        
        # Set classifier to eval mode but keep BatchNorm in training mode
        self.classifer.train()
        for p in self.classifer.parameters():
            p.requires_grad = False
        
        # Initialize Adam optimizer for generator
        self.optimizer_G = torch.optim.Adam(self.generator.parameters(), lr=0.001)
        
        # Create necessary directories
        if not os.path.exists(models_path):
            os.makedirs(models_path)
        if not os.path.exists(adv_img_path):
            os.makedirs(adv_img_path)

    def train_batch(self, x):
        """Train generator on a single batch of images.
        
        Args:
            x (torch.Tensor): Batch of input images
            
        Returns:
            tuple: (adversarial loss value, generated adversarial images, classifier predictions)
        """
        # Reset gradients
        self.optimizer_G.zero_grad()
        
        # Generate adversarial images
        adv_imgs = self.generator(x)
        
        # Compute features and predictions (no gradient computation needed)
        with torch.no_grad():
            class_out = self.classifer(adv_imgs)
            tagged_feature = self.model_extractor(x)
        
        # Extract features from adversarial images
        adv_img_feature = self.model_extractor(adv_imgs)
        
        # Compute adversarial loss
        loss_adv = F.l1_loss(tagged_feature, adv_img_feature * cfg.noise_coeff)
        loss_adv.backward(retain_graph=True)
        
        # Update generator
        self.optimizer_G.step()
        
        return loss_adv.item(), adv_imgs, class_out

    def train(self, train_dataloader, epochs):
        """Train the generator for multiple epochs.
        
        Args:
            train_dataloader (DataLoader): DataLoader for training data
            epochs (int): Number of epochs to train for
        """
        for epoch in range(1, epochs + 1):
            # Learning rate scheduling
            if epoch == 200:
                self.optimizer_G = torch.optim.Adam(self.generator.parameters(), lr=0.0001)
            if epoch == 400:
                self.optimizer_G = torch.optim.Adam(self.generator.parameters(), lr=0.00001)
            
            # Initialize epoch statistics
            loss_adv_sum = 0
            self.ite = epoch
            correct = 0
            total = 0
            
            # Train on batches
            for i, data in enumerate(train_dataloader, start=0):
                images, labels = data
                images, labels = images.to(self.device), labels.to(self.device)
                
                # Train on current batch
                loss_adv_batch, adv_img, class_out = self.train_batch(images)
                loss_adv_sum += loss_adv_batch
                
                # Calculate classification accuracy
                predicted_classes = torch.max(class_out, 1)[1]
                correct += (predicted_classes == labels).sum().item()
                total += labels.size(0)
            
            # Save sample images for visualization
            torchvision.utils.save_image(
                torch.cat((adv_img[:7], images[:7])),
                adv_img_path + str(epoch) + ".png",
                normalize=True, scale_each=True, nrow=7
            )
            
            # Print epoch statistics
            num_batch = len(train_dataloader)
            print("epoch %d:\n loss_adv: %.3f, \n" %
                  (epoch, loss_adv_sum / num_batch))
            print(f"Classification ACC: {correct / total}")
            
            # Save model checkpoint every 20 epochs
            if epoch % 20 == 0:
                netG_file_name = models_path + 'netG_epoch_' + str(epoch) + '.pth'
                torch.save(self.generator.state_dict(), netG_file_name)
                
                # Generate and save demo of poisoned samples
                trigger_img = torch.squeeze(torch.load('data/tag.pth'))
                noised_trigger_img = self.generator(torch.unsqueeze(trigger_img, 0))
                torchvision.utils.save_image(
                    (images + noised_trigger_img)[:5],
                    'data/poisoned_sample_demo.png',
                    normalize=True,
                    scale_each=True,
                    nrow=5
                )
