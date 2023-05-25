terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~>4.0"
    }
    docker = {
      source = "kreuzwerker/docker"
    }
  }
}

data "aws_region" "current" {}

data "aws_caller_identity" "this" {}

data "aws_ecr_authorization_token" "token" {}

provider "aws" {
  region = "us-east-1"

  # Make it faster by skipping something
  skip_metadata_api_check     = true
  skip_region_validation      = true
  skip_credentials_validation = true
  skip_requesting_account_id  = true
}

provider "docker" {
  registry_auth {
    address  = format("%v.dkr.ecr.%v.amazonaws.com", data.aws_caller_identity.this.account_id, data.aws_region.current.name)
    username = data.aws_ecr_authorization_token.token.user_name
    password = data.aws_ecr_authorization_token.token.password
  }
}

module "s3_bucket" {
  source = "terraform-aws-modules/s3-bucket/aws"

  bucket = var.s3_bucket_name
  acl    = "private"

  control_object_ownership = true
  object_ownership         = "ObjectWriter"

  versioning = {
    enabled = true
  }
  tags = {
    Name = "selenium-enroller"
  }
}

module "lambda_function" {
  source = "terraform-aws-modules/lambda/aws"

  function_name  = "lgcelarie-selenium-enroller-lambda"
  description    = "My enroller function"
  timeout        = 900
  create_package = false
  publish        = true

  image_uri    = module.docker_image.image_uri
  package_type = "Image"

  environment_variables = {
    "TARGET_URL"     = var.target_url
    "S3_BUCKET_NAME" = module.s3_bucket.s3_bucket_id
  }
  attach_policy_statements = true
  policy_statements = {
    s3_read = {
      effect = "Allow",
      actions = [
        "s3:GetObject"
      ],
      resources = ["${module.s3_bucket.s3_bucket_arn}/*"]
    }
  }

  allowed_triggers = {
    EventBridge = {
      principal  = "events.amazonaws.com"
      source_arn = module.eventbridge.eventbridge_rule_arns["crons"]
    }
  }

  tags = {
    Name = "selenium-enroller"
  }

}

module "docker_image" {
  source = "terraform-aws-modules/lambda/aws//modules/docker-build"

  create_ecr_repo = true
  ecr_repo        = random_pet.this.id
  ecr_repo_lifecycle_policy = jsonencode({
    "rules" : [
      {
        "rulePriority" : 1,
        "description" : "Keep only the last 2 images",
        "selection" : {
          "tagStatus" : "any",
          "countType" : "imageCountMoreThan",
          "countNumber" : 2
        },
        "action" : {
          "type" : "expire"
        }
      }
    ]
  })

  image_tag   = "2.01"
  source_path = path.cwd
  # docker_file_path = "${path.cwd}/Dockerfile"
  #   build_args = {
  #     FOO = "bar"
  #   }
  platform = "linux/amd64"
}

module "eventbridge" {
  source = "terraform-aws-modules/eventbridge/aws"

  create_bus = false

  rules = {
    crons = {
      description         = "Trigger for Selenium enroller lambda"
      schedule_expression = "cron(0 8 28 * ? *)"
    }
  }

  targets = {
    crons = [
      {
        name  = "selenium-enroller-cron"
        arn   = module.lambda_function.lambda_function_arn
        input = jsonencode({ "job" : "cron-by-schedule" })
      }
    ]
  }

  tags = {
    Name = "selenium-enroller"
  }
}

resource "random_pet" "this" {
  length = 2
}