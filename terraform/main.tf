terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# API Gateway
resource "aws_api_gateway_rest_api" "digisafe_api" {
  name        = "digisafe-api-gateway"
  description = "DigiSafe Microservices API Gateway"
}

# API Gateway Root Resource
resource "aws_api_gateway_resource" "api_root" {
  rest_api_id = aws_api_gateway_rest_api.digisafe_api.id
  parent_id   = aws_api_gateway_rest_api.digisafe_api.root_resource_id
  path_part   = "api"
}

# Search Resource
resource "aws_api_gateway_resource" "search" {
  rest_api_id = aws_api_gateway_rest_api.digisafe_api.id
  parent_id   = aws_api_gateway_resource.api_root.id
  path_part   = "search"
}

# Auction Resource
resource "aws_api_gateway_resource" "auction" {
  rest_api_id = aws_api_gateway_rest_api.digisafe_api.id
  parent_id   = aws_api_gateway_resource.api_root.id
  path_part   = "auction"
}

resource "aws_api_gateway_resource" "auction_select" {
  rest_api_id = aws_api_gateway_rest_api.digisafe_api.id
  parent_id   = aws_api_gateway_resource.auction.id
  path_part   = "select"
}

resource "aws_api_gateway_resource" "auction_search_id" {
  rest_api_id = aws_api_gateway_rest_api.digisafe_api.id
  parent_id   = aws_api_gateway_resource.auction.id
  path_part   = "{searchId}"
}

# Reward Resource
resource "aws_api_gateway_resource" "reward" {
  rest_api_id = aws_api_gateway_rest_api.digisafe_api.id
  parent_id   = aws_api_gateway_resource.api_root.id
  path_part   = "reward"
}

# Rewards Resource
resource "aws_api_gateway_resource" "rewards" {
  rest_api_id = aws_api_gateway_rest_api.digisafe_api.id
  parent_id   = aws_api_gateway_resource.api_root.id
  path_part   = "rewards"
}

resource "aws_api_gateway_resource" "rewards_claim" {
  rest_api_id = aws_api_gateway_rest_api.digisafe_api.id
  parent_id   = aws_api_gateway_resource.rewards.id
  path_part   = "claim"
}

# Verify Resource
resource "aws_api_gateway_resource" "verify" {
  rest_api_id = aws_api_gateway_rest_api.digisafe_api.id
  parent_id   = aws_api_gateway_resource.api_root.id
  path_part   = "verify"
}

# User Resource
resource "aws_api_gateway_resource" "user" {
  rest_api_id = aws_api_gateway_rest_api.digisafe_api.id
  parent_id   = aws_api_gateway_resource.api_root.id
  path_part   = "user"
}

resource "aws_api_gateway_resource" "user_dashboard" {
  rest_api_id = aws_api_gateway_rest_api.digisafe_api.id
  parent_id   = aws_api_gateway_resource.user.id
  path_part   = "dashboard"
}

# VPC Link for internal services
resource "aws_api_gateway_vpc_link" "digisafe_vpc_link" {
  name               = "digisafe-vpc-link"
  target_arns        = [aws_lb.digisafe_alb.arn]
  subnet_ids         = var.private_subnet_ids
  security_group_ids = [aws_security_group.api_gateway.id]
}

# Application Load Balancer
resource "aws_lb" "digisafe_alb" {
  name               = "digisafe-alb"
  internal           = true
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.private_subnet_ids
}

# Target Groups
resource "aws_lb_target_group" "analysis_service" {
  name     = "analysis-service-tg"
  port     = 8001
  protocol = "HTTP"
  vpc_id   = var.vpc_id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }
}

resource "aws_lb_target_group" "auction_service" {
  name     = "auction-service-tg"
  port     = 8002
  protocol = "HTTP"
  vpc_id   = var.vpc_id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }
}

resource "aws_lb_target_group" "payment_service" {
  name     = "payment-service-tg"
  port     = 8003
  protocol = "HTTP"
  vpc_id   = var.vpc_id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }
}

resource "aws_lb_target_group" "verification_service" {
  name     = "verification-service-tg"
  port     = 8004
  protocol = "HTTP"
  vpc_id   = var.vpc_id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }
}

resource "aws_lb_target_group" "user_service" {
  name     = "user-service-tg"
  port     = 8005
  protocol = "HTTP"
  vpc_id   = var.vpc_id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }
}

# ALB Listeners
resource "aws_lb_listener" "analysis_service" {
  load_balancer_arn = aws_lb.digisafe_alb.arn
  port              = 8001
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.analysis_service.arn
  }
}

resource "aws_lb_listener" "auction_service" {
  load_balancer_arn = aws_lb.digisafe_alb.arn
  port              = 8002
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.auction_service.arn
  }
}

resource "aws_lb_listener" "payment_service" {
  load_balancer_arn = aws_lb.digisafe_alb.arn
  port              = 8003
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.payment_service.arn
  }
}

resource "aws_lb_listener" "verification_service" {
  load_balancer_arn = aws_lb.digisafe_alb.arn
  port              = 8004
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.verification_service.arn
  }
}

resource "aws_lb_listener" "user_service" {
  load_balancer_arn = aws_lb.digisafe_alb.arn
  port              = 8005
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.user_service.arn
  }
}

# API Gateway Methods
resource "aws_api_gateway_method" "search_post" {
  rest_api_id   = aws_api_gateway_rest_api.digisafe_api.id
  resource_id   = aws_api_gateway_resource.search.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_method" "auction_select_post" {
  rest_api_id   = aws_api_gateway_rest_api.digisafe_api.id
  resource_id   = aws_api_gateway_resource.auction_select.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_method" "auction_search_id_get" {
  rest_api_id   = aws_api_gateway_rest_api.digisafe_api.id
  resource_id   = aws_api_gateway_resource.auction_search_id.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_method" "reward_post" {
  rest_api_id   = aws_api_gateway_rest_api.digisafe_api.id
  resource_id   = aws_api_gateway_resource.reward.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_method" "reward_get" {
  rest_api_id   = aws_api_gateway_rest_api.digisafe_api.id
  resource_id   = aws_api_gateway_resource.reward.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_method" "rewards_claim_post" {
  rest_api_id   = aws_api_gateway_rest_api.digisafe_api.id
  resource_id   = aws_api_gateway_resource.rewards_claim.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_method" "verify_post" {
  rest_api_id   = aws_api_gateway_rest_api.digisafe_api.id
  resource_id   = aws_api_gateway_resource.verify.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_method" "user_dashboard_get" {
  rest_api_id   = aws_api_gateway_rest_api.digisafe_api.id
  resource_id   = aws_api_gateway_resource.user_dashboard.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_method" "user_dashboard_post" {
  rest_api_id   = aws_api_gateway_rest_api.digisafe_api.id
  resource_id   = aws_api_gateway_resource.user_dashboard.id
  http_method   = "POST"
  authorization = "NONE"
}

# API Gateway Integrations
resource "aws_api_gateway_integration" "search_integration" {
  rest_api_id = aws_api_gateway_rest_api.digisafe_api.id
  resource_id = aws_api_gateway_resource.search.id
  http_method = aws_api_gateway_method.search_post.http_method

  type                    = "HTTP_PROXY"
  integration_http_method = "POST"
  uri                     = "http://${aws_lb.digisafe_alb.dns_name}:8001/evaluate"
  connection_type         = "VPC_LINK"
  connection_id           = aws_api_gateway_vpc_link.digisafe_vpc_link.id
}

resource "aws_api_gateway_integration" "auction_select_integration" {
  rest_api_id = aws_api_gateway_rest_api.digisafe_api.id
  resource_id = aws_api_gateway_resource.auction_select.id
  http_method = aws_api_gateway_method.auction_select_post.http_method

  type                    = "HTTP_PROXY"
  integration_http_method = "POST"
  uri                     = "http://${aws_lb.digisafe_alb.dns_name}:8002/select"
  connection_type         = "VPC_LINK"
  connection_id           = aws_api_gateway_vpc_link.digisafe_vpc_link.id
}

resource "aws_api_gateway_integration" "auction_search_id_integration" {
  rest_api_id = aws_api_gateway_rest_api.digisafe_api.id
  resource_id = aws_api_gateway_resource.auction_search_id.id
  http_method = aws_api_gateway_method.auction_search_id_get.http_method

  type                    = "HTTP_PROXY"
  integration_http_method = "GET"
  uri                     = "http://${aws_lb.digisafe_alb.dns_name}:8002/status/{searchId}"
  connection_type         = "VPC_LINK"
  connection_id           = aws_api_gateway_vpc_link.digisafe_vpc_link.id
}

resource "aws_api_gateway_integration" "reward_post_integration" {
  rest_api_id = aws_api_gateway_rest_api.digisafe_api.id
  resource_id = aws_api_gateway_resource.reward.id
  http_method = aws_api_gateway_method.reward_post.http_method

  type                    = "HTTP_PROXY"
  integration_http_method = "POST"
  uri                     = "http://${aws_lb.digisafe_alb.dns_name}:8003/reward"
  connection_type         = "VPC_LINK"
  connection_id           = aws_api_gateway_vpc_link.digisafe_vpc_link.id
}

resource "aws_api_gateway_integration" "reward_get_integration" {
  rest_api_id = aws_api_gateway_rest_api.digisafe_api.id
  resource_id = aws_api_gateway_resource.reward.id
  http_method = aws_api_gateway_method.reward_get.http_method

  type                    = "HTTP_PROXY"
  integration_http_method = "GET"
  uri                     = "http://${aws_lb.digisafe_alb.dns_name}:8003/transactions"
  connection_type         = "VPC_LINK"
  connection_id           = aws_api_gateway_vpc_link.digisafe_vpc_link.id
}

resource "aws_api_gateway_integration" "rewards_claim_integration" {
  rest_api_id = aws_api_gateway_rest_api.digisafe_api.id
  resource_id = aws_api_gateway_resource.rewards_claim.id
  http_method = aws_api_gateway_method.rewards_claim_post.http_method

  type                    = "HTTP_PROXY"
  integration_http_method = "POST"
  uri                     = "http://${aws_lb.digisafe_alb.dns_name}:8004/claim"
  connection_type         = "VPC_LINK"
  connection_id           = aws_api_gateway_vpc_link.digisafe_vpc_link.id
}

resource "aws_api_gateway_integration" "verify_integration" {
  rest_api_id = aws_api_gateway_rest_api.digisafe_api.id
  resource_id = aws_api_gateway_resource.verify.id
  http_method = aws_api_gateway_method.verify_post.http_method

  type                    = "HTTP_PROXY"
  integration_http_method = "POST"
  uri                     = "http://${aws_lb.digisafe_alb.dns_name}:8004/verify"
  connection_type         = "VPC_LINK"
  connection_id           = aws_api_gateway_vpc_link.digisafe_vpc_link.id
}

resource "aws_api_gateway_integration" "user_dashboard_get_integration" {
  rest_api_id = aws_api_gateway_rest_api.digisafe_api.id
  resource_id = aws_api_gateway_resource.user_dashboard.id
  http_method = aws_api_gateway_method.user_dashboard_get.http_method

  type                    = "HTTP_PROXY"
  integration_http_method = "GET"
  uri                     = "http://${aws_lb.digisafe_alb.dns_name}:8005/dashboard"
  connection_type         = "VPC_LINK"
  connection_id           = aws_api_gateway_vpc_link.digisafe_vpc_link.id
}

resource "aws_api_gateway_integration" "user_dashboard_post_integration" {
  rest_api_id = aws_api_gateway_rest_api.digisafe_api.id
  resource_id = aws_api_gateway_resource.user_dashboard.id
  http_method = aws_api_gateway_method.user_dashboard_post.http_method

  type                    = "HTTP_PROXY"
  integration_http_method = "POST"
  uri                     = "http://${aws_lb.digisafe_alb.dns_name}:8005/earnings"
  connection_type         = "VPC_LINK"
  connection_id           = aws_api_gateway_vpc_link.digisafe_vpc_link.id
}

# API Gateway Deployment
resource "aws_api_gateway_deployment" "digisafe_deployment" {
  depends_on = [
    aws_api_gateway_integration.search_integration,
    aws_api_gateway_integration.auction_select_integration,
    aws_api_gateway_integration.auction_search_id_integration,
    aws_api_gateway_integration.reward_post_integration,
    aws_api_gateway_integration.reward_get_integration,
    aws_api_gateway_integration.rewards_claim_integration,
    aws_api_gateway_integration.verify_integration,
    aws_api_gateway_integration.user_dashboard_get_integration,
    aws_api_gateway_integration.user_dashboard_post_integration,
  ]

  rest_api_id = aws_api_gateway_rest_api.digisafe_api.id
  stage_name  = "prod"
}

# Security Groups
resource "aws_security_group" "api_gateway" {
  name_prefix = "api-gateway-"
  vpc_id      = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "alb" {
  name_prefix = "alb-"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 8001
    to_port         = 8005
    protocol        = "tcp"
    security_groups = [aws_security_group.api_gateway.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Outputs
output "api_gateway_url" {
  value = "${aws_api_gateway_deployment.digisafe_deployment.invoke_url}"
}

output "alb_dns_name" {
  value = aws_lb.digisafe_alb.dns_name
} 