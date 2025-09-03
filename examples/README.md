# Yesman Configuration Examples

This directory contains examples showing how to configure Yesman for different development scenarios. The examples progress from simple to complex configurations.

## 📚 Learning Path - Start Here

Follow these numbered examples in order to learn Yesman configuration:

### 1. **[01-basic-session.yaml](./01-basic-session.yaml)** - Start Here!
- **Learn**: Basic session setup with minimal configuration  
- **Features**: Single session, simple window layout, basic logging
- **Best for**: Quick start, single-project development

### 2. **[02-multi-window-session.yaml](./02-multi-window-session.yaml)** 
- **Learn**: Multiple windows with different layouts and environment variables
- **Features**: Multiple windows, layout options, environment configuration
- **Best for**: Web development, need multiple terminal contexts

### 3. **[03-workspace-integration.yaml](./03-workspace-integration.yaml)**
- **Learn**: Workspace configuration for secure AI tool sandboxing
- **Features**: `workspace_config`, security policies, path restrictions
- **Best for**: AI-assisted development, team collaboration

### 4. **[04-multiple-sessions.yaml](./04-multiple-sessions.yaml)**  
- **Learn**: Managing multiple projects with different session configurations
- **Features**: Multiple sessions, different environments per session
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

All examples follow this simplified structure:

```yaml
# Basic metadata
session_name: "project-name"
description: "Project description"

# Global settings
mode: "local"              # local | merge | isolated
root_dir: "~/.scripton/yesman"

# Workspace configuration (optional - for AI tools)
workspace_config:          # Structured approach
  base_directory: "~/projects/my-app"
  definitions:
    frontend:
      path: "./frontend"
      allowed_paths: ["."]

# OR flat workspace syntax (alternative)
workspaces:                 # Flat approach
  frontend:
    path: "~/projects/my-app/frontend"
    allowed_paths: ["."]

# Session definitions
sessions:
  main:
    session_name: "main"
    start_directory: "~/projects/my-app"
    
    # Optional setup/cleanup scripts
    before_script: |
      echo "Starting environment..."
    after_script: |
      echo "Cleaning up..."
    
    # Environment variables
    environment:
      NODE_ENV: "development"
    
    # Window and pane layout
    windows:
      - window_name: "editor"
        layout: "main-vertical"  # even-horizontal | main-horizontal | tiled
        start_directory: "./src"
        panes:
          - bash
          - npm run dev

# Logging configuration
logging:
  level: "INFO"
  file: "~/.scripton/yesman/logs/project.log"
```

## 🔧 Configuration Options

### Session Modes
- **`local`**: Use local configuration only
- **`merge`**: Merge with global/template configurations  
- **`isolated`**: Fully isolated environment

### Window Layouts  
- **`even-horizontal`**: Split panes horizontally with equal size
- **`even-vertical`**: Split panes vertically with equal size
- **`main-horizontal`**: Main pane on top, others split below
- **`main-vertical`**: Main pane on left, others split right
- **`tiled`**: Automatic tiling layout

### Workspace Security Policies
- **`default`**: Standard security restrictions
- **`strict`**: Enhanced security for sensitive projects
- **`restricted`**: Maximum security, limited access

### Workspace Types

#### Structured Workspaces (`workspace_config`)
```yaml
workspace_config:
  base_directory: "~/projects/app"
  definitions:
    frontend:
      path: "./frontend"          # Relative to base_directory
      allowed_paths: ["."]
```

#### Flat Workspaces (`workspaces`)  
```yaml
workspaces:
  frontend:
    path: "~/projects/app/frontend"  # Absolute path
    allowed_paths: ["."]
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
Organize different projects in separate sessions:
```yaml
sessions:
  frontend:
    session_name: "frontend"
    start_directory: "~/projects/frontend"
  backend:
    session_name: "backend" 
    start_directory: "~/projects/backend"
```

## ⚠️ Migration from Legacy Examples

If you're using older Yesman configurations, note these changes:

- **`templates:` removed** → Use direct session configuration
- **`claude:` renamed** → Use `workspace_config:` or `workspaces:`
- **Template system simplified** → Use numbered examples as templates

Legacy files are marked as DEPRECATED and should be replaced with numbered examples.

## 🆘 Getting Help

- **Validate config**: `./yesman.py validate`
- **List sessions**: `./yesman.py ls` 
- **Test session**: `./yesman.py setup session-name --dry-run`
- **View status**: `./yesman.py status`

For more detailed information, run `./yesman.py --help` or see the main project documentation.