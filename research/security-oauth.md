# OAuth 2.1 Security for MCP Servers

## Overview

The June 2025 MCP specification (version 2025-06-18) officially mandates OAuth 2.1 for remote MCP servers. This document covers OAuth implementation, security best practices, and integration patterns.

## Why OAuth 2.1?

OAuth 2.1 consolidates best practices from OAuth 2.0 and incorporates security improvements:

- **PKCE required**: Prevents authorization code interception
- **No implicit flow**: Removed insecure grant type
- **Token rotation**: Refresh tokens are single-use
- **Resource Indicators**: Prevent token theft (RFC 8707)
- **Secure by default**: Modern security patterns built-in

## MCP-Specific OAuth Requirements

### MCP Servers as Resource Servers

Per the 2025-06-18 specification:

> "MCP servers are now officially classified as OAuth Resource Servers"

This means your MCP server must:

1. **Validate access tokens** on every request
2. **Implement Resource Indicators** (RFC 8707)
3. **Support token introspection** (optional but recommended)
4. **Enforce proper scopes**
5. **Return appropriate error responses**

### Resource Indicators (RFC 8707)

**Problem**: Malicious MCP servers could steal access tokens intended for other services.

**Solution**: Resource Indicators ensure tokens are scoped to specific MCP servers.

**Implementation**:
```http
# Authorization request includes resource parameter
GET /authorize?
  response_type=code
  &client_id=CLIENT_ID
  &redirect_uri=https://client.example.com/callback
  &resource=https://mcp-github.yourdomain.com
  &resource=https://mcp-n8n.yourdomain.com
  &scope=mcp:tools mcp:resources
```

The authorization server issues tokens that can ONLY be used with the specified resources.

## OAuth Flow for MCP

### 1. Authorization Code Flow with PKCE

**Recommended for**: MCP clients (like Claude Desktop) accessing remote MCP servers

```
┌─────────────┐                                  ┌──────────────────┐
│ MCP Client  │                                  │  Authorization   │
│  (Claude)   │                                  │     Server       │
└──────┬──────┘                                  └────────┬─────────┘
       │                                                  │
       │ 1. Generate code_verifier                       │
       │    code_challenge = SHA256(code_verifier)       │
       │                                                  │
       │ 2. GET /authorize?                              │
       │    response_type=code                           │
       │    &client_id=...                               │
       │    &redirect_uri=...                            │
       │    &code_challenge=...                          │
       │    &code_challenge_method=S256                  │
       │    &resource=https://mcp.example.com            │
       │    &scope=mcp:tools mcp:resources               │
       ├────────────────────────────────────────────────>│
       │                                                  │
       │ 3. User authenticates & authorizes              │
       │                                                  │
       │ 4. Redirect with authorization code             │
       │<─────────────────────────────────────────────────┤
       │    https://client.app/callback?code=ABC123      │
       │                                                  │
       │ 5. POST /token                                  │
       │    grant_type=authorization_code                │
       │    &code=ABC123                                 │
       │    &redirect_uri=...                            │
       │    &code_verifier=original_verifier             │
       │    &client_id=...                               │
       ├────────────────────────────────────────────────>│
       │                                                  │
       │ 6. Access token + refresh token                 │
       │<─────────────────────────────────────────────────┤
       │    {"access_token": "...",                      │
       │     "refresh_token": "...",                     │
       │     "expires_in": 3600}                         │
       │                                                  │
       ▼                                                  ▼

┌──────────────┐
│ MCP Server   │
└──────┬───────┘
       │
       │ 7. Request with token
       │    Authorization: Bearer <access_token>
       │<────────────────────
       │
       │ 8. Validate token
       │    - Check signature
       │    - Check expiration
       │    - Check resource (RFC 8707)
       │    - Check scopes
       │
       │ 9. Return response
       │──────────────────────>
```

### 2. Client Credentials Flow

**Recommended for**: Server-to-server MCP communication (e.g., n8n calling MCP server)

```
┌─────────────┐                                  ┌──────────────────┐
│ MCP Client  │                                  │  Authorization   │
│  (Server)   │                                  │     Server       │
└──────┬──────┘                                  └────────┬─────────┘
       │                                                  │
       │ 1. POST /token                                  │
       │    grant_type=client_credentials                │
       │    &client_id=...                               │
       │    &client_secret=...                           │
       │    &scope=mcp:tools mcp:resources               │
       │    &resource=https://mcp.example.com            │
       ├────────────────────────────────────────────────>│
       │                                                  │
       │ 2. Access token                                 │
       │<─────────────────────────────────────────────────┤
       │    {"access_token": "...",                      │
       │     "expires_in": 3600}                         │
       │                                                  │
       ▼                                                  ▼
```

## Implementation: MCP Server with OAuth

### Example: Express.js MCP Server with OAuth

```javascript
import express from 'express';
import jwt from 'jsonwebtoken';
import { Server } from '@modelcontextprotocol/sdk/server/index.js';

const app = express();
const JWT_PUBLIC_KEY = process.env.JWT_PUBLIC_KEY; // From auth server
const EXPECTED_AUDIENCE = process.env.MCP_SERVER_URL; // Resource Indicator

// ============================================================================
// OAuth Middleware
// ============================================================================

async function validateToken(req, res, next) {
  const authHeader = req.headers.authorization;

  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({
      error: 'unauthorized',
      error_description: 'Missing or invalid Authorization header',
    });
  }

  const token = authHeader.substring(7); // Remove 'Bearer '

  try {
    // Verify JWT signature
    const decoded = jwt.verify(token, JWT_PUBLIC_KEY, {
      algorithms: ['RS256'], // OAuth 2.1 requires RS256 or better
    });

    // Validate Resource Indicator (RFC 8707)
    if (decoded.aud !== EXPECTED_AUDIENCE) {
      return res.status(403).json({
        error: 'invalid_token',
        error_description: `Token not valid for this resource. Expected: ${EXPECTED_AUDIENCE}`,
      });
    }

    // Validate expiration
    if (decoded.exp && decoded.exp < Date.now() / 1000) {
      return res.status(401).json({
        error: 'invalid_token',
        error_description: 'Token expired',
      });
    }

    // Validate scopes
    const requiredScopes = ['mcp:tools', 'mcp:resources'];
    const tokenScopes = decoded.scope ? decoded.scope.split(' ') : [];

    const hasRequiredScopes = requiredScopes.every((scope) =>
      tokenScopes.includes(scope)
    );

    if (!hasRequiredScopes) {
      return res.status(403).json({
        error: 'insufficient_scope',
        error_description: `Required scopes: ${requiredScopes.join(', ')}`,
      });
    }

    // Attach user info to request
    req.user = {
      sub: decoded.sub,
      scopes: tokenScopes,
      clientId: decoded.client_id,
    };

    next();
  } catch (error) {
    console.error('Token validation error:', error);
    return res.status(401).json({
      error: 'invalid_token',
      error_description: error.message,
    });
  }
}

// ============================================================================
// MCP Endpoints with OAuth
// ============================================================================

// Public endpoint (no auth required)
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

// Protected MCP endpoints
app.use('/mcp', validateToken);

app.get('/mcp/v1/tools/list', validateToken, async (req, res) => {
  // User info available in req.user
  console.log(`Tools list requested by user: ${req.user.sub}`);

  // Return tools based on user's scopes
  const tools = getToolsForScopes(req.user.scopes);

  res.json({ tools });
});

app.post('/mcp/v1/tools/call', validateToken, async (req, res) => {
  const { name, arguments: args } = req.body;

  // Check if user has permission for this specific tool
  if (!canAccessTool(req.user, name)) {
    return res.status(403).json({
      error: 'forbidden',
      error_description: `User does not have access to tool: ${name}`,
    });
  }

  // Execute tool
  const result = await executeTool(name, args, req.user);

  res.json({ result });
});

// ============================================================================
// Audit Logging
// ============================================================================

function auditLog(req, action, details = {}) {
  const logEntry = {
    timestamp: new Date().toISOString(),
    user: req.user?.sub,
    clientId: req.user?.clientId,
    action,
    ip: req.ip,
    userAgent: req.headers['user-agent'],
    ...details,
  };

  console.log('AUDIT:', JSON.stringify(logEntry));

  // Store in database for compliance
  saveAuditLog(logEntry);
}

app.post('/mcp/v1/tools/call', validateToken, async (req, res) => {
  auditLog(req, 'tool_call', {
    toolName: req.body.name,
    arguments: req.body.arguments,
  });

  // ... execute tool
});
```

### Token Introspection (Optional)

For enhanced security, validate tokens with the authorization server:

```javascript
async function introspectToken(token) {
  const response = await fetch('https://auth.example.com/oauth/introspect', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      Authorization: `Basic ${Buffer.from(`${CLIENT_ID}:${CLIENT_SECRET}`).toString('base64')}`,
    },
    body: new URLSearchParams({
      token,
      token_type_hint: 'access_token',
    }),
  });

  const result = await response.json();

  if (!result.active) {
    throw new Error('Token is not active');
  }

  return result;
}

// Use in middleware
async function validateToken(req, res, next) {
  const token = extractToken(req);

  try {
    const tokenInfo = await introspectToken(token);

    req.user = {
      sub: tokenInfo.sub,
      scopes: tokenInfo.scope.split(' '),
      clientId: tokenInfo.client_id,
    };

    next();
  } catch (error) {
    return res.status(401).json({ error: 'invalid_token' });
  }
}
```

## Integration with Cloudflare Zero Trust

### Architecture: Multi-Layer Security

```
┌──────────────────┐
│   MCP Client     │
└────────┬─────────┘
         │
         │ HTTPS
         ▼
┌──────────────────────────────┐
│  Cloudflare Zero Trust       │ Layer 1: Identity
│  - Email verification        │
│  - 2FA                        │
│  - Device posture             │
└────────┬─────────────────────┘
         │
         │ Cloudflare Tunnel
         ▼
┌──────────────────────────────┐
│  MCP Server OAuth Layer      │ Layer 2: Authorization
│  - Token validation          │
│  - Scope checking            │
│  - Resource indicators       │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│  MCP Server Logic            │ Layer 3: Business Logic
│  - Tools execution           │
│  - Resource access           │
└──────────────────────────────┘
```

### Benefits of Multi-Layer Security

1. **Zero Trust**: Identity verification before reaching your network
2. **OAuth**: Fine-grained authorization for MCP operations
3. **Audit Trail**: Complete logs at both layers
4. **Defense in Depth**: Multiple security controls

### Configuration Example

**Cloudflare Zero Trust Policy**:
```
Application: mcp-github.yourdomain.com
Policy:
  - Allow: Emails ending in @yourcompany.com
  - Require: GitHub authentication with 2FA
  - Session: 8 hours
  - Country: Allowed list
```

**MCP Server OAuth Scopes**:
```javascript
const scopePermissions = {
  'mcp:tools:read': ['list_tools', 'get_tool_schema'],
  'mcp:tools:execute': ['call_tool'],
  'mcp:resources:read': ['list_resources', 'read_resource'],
  'mcp:workflows:write': ['create_workflow', 'update_workflow'],
};
```

## Scopes Best Practices

### Standard MCP Scopes

```
mcp:tools:read       - List available tools
mcp:tools:execute    - Execute tools
mcp:resources:read   - Read resources
mcp:resources:write  - Modify resources
mcp:prompts:read     - Access prompt templates
mcp:admin            - Administrative operations
```

### Granular Scopes

```
mcp:github:issues:read
mcp:github:issues:write
mcp:github:repos:read
mcp:database:query
mcp:database:write
mcp:n8n:workflows:read
mcp:n8n:workflows:execute
```

### Scope Hierarchy

```javascript
const scopeHierarchy = {
  'mcp:admin': [
    'mcp:tools:read',
    'mcp:tools:execute',
    'mcp:resources:read',
    'mcp:resources:write',
    'mcp:prompts:read',
  ],
  'mcp:tools:execute': ['mcp:tools:read'],
  'mcp:resources:write': ['mcp:resources:read'],
};

function hasPermission(userScopes, requiredScope) {
  // Check direct match
  if (userScopes.includes(requiredScope)) return true;

  // Check hierarchy
  for (const userScope of userScopes) {
    const impliedScopes = scopeHierarchy[userScope] || [];
    if (impliedScopes.includes(requiredScope)) return true;
  }

  return false;
}
```

## Rate Limiting

Prevent abuse with rate limiting:

```javascript
import rateLimit from 'express-rate-limit';

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // Limit each user to 100 requests per windowMs
  keyGenerator: (req) => req.user?.sub || req.ip,
  standardHeaders: true,
  legacyHeaders: false,
  handler: (req, res) => {
    auditLog(req, 'rate_limit_exceeded');
    res.status(429).json({
      error: 'too_many_requests',
      error_description: 'Rate limit exceeded. Try again later.',
    });
  },
});

app.use('/mcp', limiter);
```

### Advanced: Per-Scope Rate Limits

```javascript
const scopeRateLimits = {
  'mcp:tools:execute': { windowMs: 60000, max: 10 }, // 10/minute
  'mcp:resources:read': { windowMs: 60000, max: 100 }, // 100/minute
  'mcp:admin': { windowMs: 60000, max: 5 }, // 5/minute
};

function getRateLimitForScope(scopes) {
  let maxRequests = 10; // Default
  let windowMs = 60000;

  for (const scope of scopes) {
    const limit = scopeRateLimits[scope];
    if (limit && limit.max > maxRequests) {
      maxRequests = limit.max;
      windowMs = limit.windowMs;
    }
  }

  return { windowMs, max: maxRequests };
}
```

## Security Checklist

### MCP Server Security

- [ ] OAuth 2.1 implemented (not OAuth 2.0)
- [ ] PKCE required for authorization code flow
- [ ] Resource Indicators (RFC 8707) validated
- [ ] JWT signatures verified (RS256 or better)
- [ ] Token expiration checked
- [ ] Scopes validated on every request
- [ ] Audit logging implemented
- [ ] Rate limiting configured
- [ ] HTTPS only (no HTTP)
- [ ] Input validation on all tool parameters
- [ ] Error messages don't leak sensitive info

### OAuth Provider Security

- [ ] Strong client secrets (32+ random characters)
- [ ] Client credentials stored securely (env vars, secrets manager)
- [ ] Refresh token rotation enabled
- [ ] Short-lived access tokens (≤ 1 hour)
- [ ] Revocation endpoint implemented
- [ ] Token introspection available
- [ ] Audit logs retained (90+ days recommended)

### Infrastructure Security

- [ ] Cloudflare Tunnel (no port forwarding)
- [ ] Zero Trust access policies configured
- [ ] TLS 1.3 enforced
- [ ] Security headers set (HSTS, CSP, etc.)
- [ ] Regular security updates
- [ ] Secrets not in Git
- [ ] Environment-specific credentials (dev/prod)

## OAuth Providers

### Option 1: Cloudflare Access

Built-in OAuth with Cloudflare Zero Trust:

```
https://your-team.cloudflareaccess.com/cdn-cgi/access/
```

**Pros**:
- Integrated with Cloudflare Tunnel
- No additional infrastructure
- Multiple identity providers

**Cons**:
- Limited customization
- Cloudflare-specific

### Option 2: Self-Hosted (ORY Hydra)

```bash
docker run -p 4444:4444 \
  -e DSN=postgres://... \
  oryd/hydra:latest serve all
```

**Pros**:
- Full control
- Open source
- Standards-compliant

**Cons**:
- Requires maintenance
- Additional infrastructure

### Option 3: Auth0, Okta, etc.

Commercial OAuth providers.

**Pros**:
- Managed service
- Rich features
- Good documentation

**Cons**:
- Monthly cost
- Vendor lock-in

## Testing OAuth

### Manual Testing

```bash
# 1. Get authorization code (open in browser)
https://auth.example.com/authorize?
  response_type=code
  &client_id=YOUR_CLIENT_ID
  &redirect_uri=http://localhost:8080/callback
  &code_challenge=CHALLENGE
  &code_challenge_method=S256
  &resource=https://mcp.yourdomain.com
  &scope=mcp:tools mcp:resources

# 2. Exchange code for token
curl -X POST https://auth.example.com/token \
  -d grant_type=authorization_code \
  -d code=RECEIVED_CODE \
  -d redirect_uri=http://localhost:8080/callback \
  -d client_id=YOUR_CLIENT_ID \
  -d code_verifier=ORIGINAL_VERIFIER

# 3. Use token
curl -H "Authorization: Bearer ACCESS_TOKEN" \
  https://mcp.yourdomain.com/mcp/v1/tools/list
```

### Automated Testing

```javascript
// test/oauth.test.js
import { describe, it, expect } from 'vitest';
import jwt from 'jsonwebtoken';

describe('OAuth Middleware', () => {
  it('should reject requests without token', async () => {
    const res = await fetch('http://localhost:3000/mcp/v1/tools/list');
    expect(res.status).toBe(401);
  });

  it('should reject expired tokens', async () => {
    const expiredToken = jwt.sign({ sub: 'user123', exp: 0 }, privateKey);

    const res = await fetch('http://localhost:3000/mcp/v1/tools/list', {
      headers: { Authorization: `Bearer ${expiredToken}` },
    });

    expect(res.status).toBe(401);
  });

  it('should reject tokens with wrong audience', async () => {
    const token = jwt.sign(
      { sub: 'user123', aud: 'https://wrong-resource.com' },
      privateKey
    );

    const res = await fetch('http://localhost:3000/mcp/v1/tools/list', {
      headers: { Authorization: `Bearer ${token}` },
    });

    expect(res.status).toBe(403);
  });

  it('should allow valid tokens', async () => {
    const validToken = jwt.sign(
      {
        sub: 'user123',
        aud: 'https://mcp.yourdomain.com',
        scope: 'mcp:tools mcp:resources',
        exp: Math.floor(Date.now() / 1000) + 3600,
      },
      privateKey
    );

    const res = await fetch('http://localhost:3000/mcp/v1/tools/list', {
      headers: { Authorization: `Bearer ${validToken}` },
    });

    expect(res.status).toBe(200);
  });
});
```

## Resources

- **RFC 8707 - Resource Indicators**: https://datatracker.ietf.org/doc/html/rfc8707
- **OAuth 2.1 Draft**: https://oauth.net/2.1/
- **MCP Specification**: https://modelcontextprotocol.io/specification/latest
- **ORY Hydra**: https://www.ory.sh/hydra/
- **Cloudflare Access**: https://developers.cloudflare.com/cloudflare-one/

---

**Document Version**: 1.0
**Last Updated**: November 8, 2025
**MCP Specification**: 2025-06-18
