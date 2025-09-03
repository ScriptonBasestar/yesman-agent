# Yesman Configuration Examples

This directory contains examples showing how to configure Yesman for different development scenarios. The examples progress from simple to complex configurations.

## 📚 Learning Path - Start Here

Follow these numbered examples in order to learn Yesman configuration:

### 1. **[01-basic-session.yaml](./01-basic-session.yaml)** - Start Here!
- **Learn**: Basic session setup with minimal configuration  
- **Features**: Single session, simple window layout, basic logging
- **Best for**: Quick start, single-project development

### 2. **[02-multi-window-session.yaml](./02-multi-window-session.yaml)** 
- **Learn**: Environment variables and session configuration
- **Features**: Environment setup, session configuration 
- **Best for**: Web development, environment management

### 3. **[03-workspace-integration.yaml](./03-workspace-integration.yaml)**
- **Learn**: Workspace configuration for secure AI tool sandboxing
- **Features**: `workspace_config`, security policies, path restrictions
- **Best for**: AI-assisted development, team collaboration

### 4. **[04-multiple-sessions.yaml](./04-multiple-sessions.yaml)**  
- **Learn**: Managing multiple projects with workspace definitions
- **Features**: Multiple workspaces, project organization
- **Best for**: Multi-project development, separating concerns

### 5. **[05-flat-workspaces.yaml](./05-flat-workspaces.yaml)**
- **Learn**: Alternative flat workspace syntax (simpler than workspace_config)
- **Features**: `workspaces:` instead of `workspace_config:`, monorepo support
- **Best for**: Monorepos, simpler workspace definitions

### 6. **[06-advanced-features.yaml](./06-advanced-features.yaml)** - Complete Guide
- **Learn**: Advanced features including scripts, custom settings, complex automation
- **Features**: `before_script`, `after_script`, advanced layouts, custom configuration
- **Best for**: Production environments, complex automation needs

## 🎯 Production Use Cases

After learning the basics, explore these production-ready configurations:

### **[use-cases/django-development.yaml](./use-cases/django-development.yaml)**
Complete Django web application development setup with database, worker processes, and testing.

### **[use-cases/data-science.yaml](./use-cases/data-science.yaml)** 
Data science and machine learning environment with Jupyter, MLflow, TensorBoard, and GPU support.

### **[use-cases/devops-monitoring.yaml](./use-cases/devops-monitoring.yaml)**
DevOps and infrastructure monitoring with Terraform, Ansible, Kubernetes, and monitoring tools.

## 🏗️ Configuration Structure

All examples follow this simplified, workspace-focused structure:

```yaml
# Basic metadata
session_name: "project-name"
description: "Project description"

# Workspace configuration (core feature - for AI tools)
workspace_config:          # Base directory config
  base_dir: "~/projects/my-app"

workspace_definitions:      # Individual workspace definitions
  frontend:
    rel_dir: "./frontend"
    allowed_paths: ["."]
    description: "Frontend workspace"

# OR flat workspace syntax (alternative)
workspaces:                 # Flat approach  
  frontend:
    rel_dir: "~/projects/my-app/frontend"
    allowed_paths: ["."]
    description: "Frontend workspace"

# Optional setup/cleanup scripts
before_script: |
  echo "Starting environment..."
  npm install
  
after_script: |
  echo "Cleaning up..."

# Environment variables
environment:
  NODE_ENV: "development"
  API_URL: "http://localhost:8000"

# Logging configuration
logging:
  level: "INFO"
  file: "~/.scripton/yesman/logs/project.log"
```

## 🔧 Configuration Options

### Workspace Security
- **`allowed_paths`**: Control which directories AI tools can access
- **`base_dir`**: Base directory for relative workspace paths  
- **Path restrictions**: Essential for secure AI tool usage

### Workspace Types

#### Structured Workspaces (Recommended)
```yaml
workspace_config:
  base_dir: "~/projects/app"

workspace_definitions:
  frontend:
    rel_dir: "./frontend"          # Relative to base_dir
    allowed_paths: ["."]
    description: "Frontend workspace"
```

#### Flat Workspaces (Alternative)
```yaml
workspaces:
  frontend:
    rel_dir: "~/projects/app/frontend"  # Absolute path
    allowed_paths: ["."]
    description: "Frontend workspace"
```

## 🚀 Getting Started

1. **Start with basics**: Copy `01-basic-session.yaml` and modify for your project
2. **Add complexity gradually**: Follow the numbered progression 
3. **Use production examples**: Adapt use-cases for your specific needs
4. **Test your configuration**: Run `./yesman.py validate` to check syntax

## 📝 Configuration Tips

### Environment Variables
Set environment variables per session:
```yaml
environment:
  NODE_ENV: "development"
  API_URL: "http://localhost:8000"
  DEBUG: "true"
```

### Custom Scripts
Automate environment setup:
```yaml
before_script: |
  npm install
  docker-compose up -d database
  
after_script: |
  docker-compose down
```

### Multiple Projects
Organize different projects with separate workspace definitions:
```yaml
workspace_config:
  base_dir: "~/projects"

workspace_definitions:
  frontend:
    rel_dir: "./frontend"
    allowed_paths: ["."]
    description: "Frontend project"
  backend:
    rel_dir: "./backend" 
    allowed_paths: ["."]
    description: "Backend project"
```

## ⚠️ Migration from Legacy Examples

If you're using older Yesman configurations, note these changes:

- **`templates:` removed** → Use direct configuration
- **`sessions:` simplified** → Use top-level session settings  
- **`claude:` renamed** → Use `workspace_config:` or `workspaces:`
- **Complex session nesting removed** → Flatter, workspace-focused structure

Legacy files are marked as DEPRECATED and should be replaced with numbered examples.

## 🆘 Getting Help

- **Validate config**: `./yesman.py validate`
- **List sessions**: `./yesman.py ls` 
- **Test session**: `./yesman.py setup session-name --dry-run`
- **View status**: `./yesman.py status`

For more detailed information, run `./yesman.py --help` or see the main project documentation.