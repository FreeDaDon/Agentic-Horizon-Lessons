# Elite Context Engineering - Comprehensive Codebase Practices Guide

## Overview
This is an example of a BLOATED CLAUDE.md file that demonstrates what happens when you try to document everything in one place. This file shows the anti-pattern of over-contextualization.

## Codebase Style Practices

### Code Syntax Standards

#### Formatting Rules
Our codebase enforces strict formatting standards across all languages:

```typescript
// CORRECT: Consistent spacing and alignment
interface UserConfiguration {
  readonly id: string;
  readonly email: string;
  readonly preferences: UserPreferences;
  readonly metadata: {
    createdAt: Date;
    updatedAt: Date;
    lastLoginAt: Date | null;
  };
}

// INCORRECT: Inconsistent formatting
interface UserConfiguration{
readonly id:string;
readonly email:string;
readonly preferences:UserPreferences;
readonly metadata:{createdAt:Date;updatedAt:Date;lastLoginAt:Date|null;};}
```

#### Indentation Standards
- Use 2 spaces for TypeScript/JavaScript
- Use 4 spaces for Python
- Use tabs for Go
- Never mix tabs and spaces in the same file
- Configure your editor to show whitespace characters
- Always use .editorconfig file for consistency

#### Line Length Rules
- Maximum 100 characters for TypeScript/JavaScript
- Maximum 88 characters for Python (Black formatter)
- Maximum 120 characters for documentation
- Break long lines at logical boundaries
- Use trailing commas for better diffs

#### Import Organization
Always organize imports in the following order:
```typescript
// 1. Node.js built-in modules
import * as fs from 'fs';
import * as path from 'path';
import * as crypto from 'crypto';

// 2. External dependencies
import express from 'express';
import { z } from 'zod';
import * as jwt from 'jsonwebtoken';
import { Decimal } from 'decimal.js';

// 3. Internal absolute imports
import { UserService } from '@/services/user-service';
import { DatabaseConnection } from '@/infrastructure/database';
import { AppError } from '@/shared/errors';

// 4. Internal relative imports
import { validateEmail } from './utils/validators';
import { formatDate } from './helpers/date-formatter';
import type { LocalConfig } from './types';

// 5. Style imports (if applicable)
import './styles/main.css';
```

#### Naming Conventions

##### Files and Directories
```typescript
// Files: kebab-case
user-service.ts
authentication-middleware.ts
create-user.dto.ts
database-connection.ts

// Directories: kebab-case
src/
  application-services/
  domain-models/
  infrastructure-layer/
  presentation-controllers/

// Test files: add .spec or .test
user-service.spec.ts
authentication-middleware.test.ts

// Configuration files: .config suffix
database.config.ts
redis.config.ts

// Type definition files: .types suffix
user.types.ts
api-response.types.ts
```

##### Variables and Functions
```typescript
// Constants: UPPER_SNAKE_CASE
const MAX_RETRY_ATTEMPTS = 3;
const DEFAULT_TIMEOUT_MS = 5000;
const API_BASE_URL = 'https://api.example.com';

// Variables: camelCase
const userCount = 42;
const isAuthenticated = true;
const responseData = await fetchData();

// Functions: camelCase, verb + noun
function calculateTotalPrice(items: Item[]): number { }
async function fetchUserProfile(userId: string): Promise<User> { }
function validateEmailFormat(email: string): boolean { }

// Private methods: underscore prefix
private _performInternalCalculation(): void { }
private _validateInternalState(): boolean { }

// Classes: PascalCase
class UserRepository { }
class AuthenticationService { }
class DatabaseConnectionPool { }

// Interfaces: PascalCase with 'I' prefix (optional but recommended)
interface IUserRepository { }
interface IAuthenticationStrategy { }
interface IDatabaseAdapter { }

// Type aliases: PascalCase
type UserId = string;
type EmailAddress = string;
type Timestamp = number;

// Enums: PascalCase for name, UPPER_SNAKE_CASE for values
enum UserRole {
  ADMIN = 'ADMIN',
  MODERATOR = 'MODERATOR',
  USER = 'USER',
  GUEST = 'GUEST'
}

// Boolean variables: use 'is', 'has', 'can', 'should' prefixes
const isValid = true;
const hasPermission = false;
const canEdit = user.role === UserRole.ADMIN;
const shouldRetry = attempts < MAX_RETRY_ATTEMPTS;
```

### Code Patterns and Idioms

#### Guard Clauses
Always use early returns for better readability:
```typescript
// GOOD: Early returns reduce nesting
function processUser(user: User | null): ProcessedUser {
  if (!user) {
    throw new Error('User is required');
  }
  
  if (user.status === 'inactive') {
    return { processed: false, reason: 'User inactive' };
  }
  
  if (!user.email || !isValidEmail(user.email)) {
    return { processed: false, reason: 'Invalid email' };
  }
  
  // Main logic here with minimal nesting
  return processActiveUser(user);
}

// BAD: Nested if statements
function processUser(user: User | null): ProcessedUser {
  if (user) {
    if (user.status !== 'inactive') {
      if (user.email && isValidEmail(user.email)) {
        // Main logic buried deep in nesting
        return processActiveUser(user);
      } else {
        return { processed: false, reason: 'Invalid email' };
      }
    } else {
      return { processed: false, reason: 'User inactive' };
    }
  } else {
    throw new Error('User is required');
  }
}
```

#### Null Handling Patterns
```typescript
// Use optional chaining and nullish coalescing
const displayName = user?.profile?.displayName ?? 'Anonymous';
const preferences = user?.settings?.preferences ?? defaultPreferences;

// Null object pattern
class NullUser implements IUser {
  readonly id = 'null';
  readonly email = '';
  readonly isNull = true;
  
  hasPermission(permission: string): boolean {
    return false;
  }
}

const user = findUser(userId) ?? new NullUser();
if (!user.isNull) {
  // Process real user
}

// Maybe/Option pattern
class Maybe<T> {
  constructor(private value: T | null | undefined) {}
  
  static of<T>(value: T | null | undefined): Maybe<T> {
    return new Maybe(value);
  }
  
  map<U>(fn: (value: T) => U): Maybe<U> {
    return this.value ? Maybe.of(fn(this.value)) : Maybe.of(null);
  }
  
  flatMap<U>(fn: (value: T) => Maybe<U>): Maybe<U> {
    return this.value ? fn(this.value) : Maybe.of(null);
  }
  
  orElse(defaultValue: T): T {
    return this.value ?? defaultValue;
  }
}

// Usage
const userName = Maybe.of(user)
  .map(u => u.profile)
  .map(p => p.displayName)
  .orElse('Anonymous');
```

#### Builder Pattern
```typescript
class EmailBuilder {
  private to: string[] = [];
  private cc: string[] = [];
  private bcc: string[] = [];
  private subject = '';
  private body = '';
  private attachments: Attachment[] = [];
  private priority: Priority = 'normal';
  
  addTo(email: string): this {
    this.to.push(email);
    return this;
  }
  
  addCc(email: string): this {
    this.cc.push(email);
    return this;
  }
  
  setSubject(subject: string): this {
    this.subject = subject;
    return this;
  }
  
  setBody(body: string): this {
    this.body = body;
    return this;
  }
  
  attachFile(file: Attachment): this {
    this.attachments.push(file);
    return this;
  }
  
  setPriority(priority: Priority): this {
    this.priority = priority;
    return this;
  }
  
  build(): Email {
    if (this.to.length === 0) {
      throw new Error('At least one recipient is required');
    }
    
    if (!this.subject) {
      throw new Error('Subject is required');
    }
    
    return new Email({
      to: this.to,
      cc: this.cc,
      bcc: this.bcc,
      subject: this.subject,
      body: this.body,
      attachments: this.attachments,
      priority: this.priority,
    });
  }
}

// Usage
const email = new EmailBuilder()
  .addTo('user@example.com')
  .addCc('manager@example.com')
  .setSubject('Monthly Report')
  .setBody('Please find attached...')
  .attachFile(reportFile)
  .setPriority('high')
  .build();
```

#### Strategy Pattern
```typescript
interface CompressionStrategy {
  compress(data: Buffer): Buffer;
  decompress(data: Buffer): Buffer;
  readonly algorithm: string;
}

class GzipStrategy implements CompressionStrategy {
  readonly algorithm = 'gzip';
  
  compress(data: Buffer): Buffer {
    return zlib.gzipSync(data);
  }
  
  decompress(data: Buffer): Buffer {
    return zlib.gunzipSync(data);
  }
}

class BrotliStrategy implements CompressionStrategy {
  readonly algorithm = 'brotli';
  
  compress(data: Buffer): Buffer {
    return zlib.brotliCompressSync(data);
  }
  
  decompress(data: Buffer): Buffer {
    return zlib.brotliDecompressSync(data);
  }
}

class CompressionContext {
  constructor(private strategy: CompressionStrategy) {}
  
  setStrategy(strategy: CompressionStrategy): void {
    this.strategy = strategy;
  }
  
  compressFile(filePath: string): void {
    const data = fs.readFileSync(filePath);
    const compressed = this.strategy.compress(data);
    fs.writeFileSync(`${filePath}.${this.strategy.algorithm}`, compressed);
  }
}

// Usage
const compression = new CompressionContext(new GzipStrategy());
compression.compressFile('data.json');

// Switch strategy based on file size
if (fileSize > 1024 * 1024) { // > 1MB
  compression.setStrategy(new BrotliStrategy());
}
```

### Testing Conventions

#### Test File Structure
```typescript
describe('UserService', () => {
  // Setup and teardown
  let service: UserService;
  let mockRepository: jest.Mocked<UserRepository>;
  let mockEventBus: jest.Mocked<EventBus>;
  
  beforeAll(async () => {
    // One-time setup
    await setupTestDatabase();
  });
  
  afterAll(async () => {
    // Cleanup
    await teardownTestDatabase();
  });
  
  beforeEach(() => {
    // Reset mocks and create fresh instances
    jest.clearAllMocks();
    mockRepository = createMock<UserRepository>();
    mockEventBus = createMock<EventBus>();
    service = new UserService(mockRepository, mockEventBus);
  });
  
  describe('createUser', () => {
    describe('with valid input', () => {
      it('should create user successfully', async () => {
        // Arrange
        const input = buildCreateUserInput();
        const expectedUser = buildUser(input);
        mockRepository.save.mockResolvedValue(expectedUser);
        
        // Act
        const result = await service.createUser(input);
        
        // Assert
        expect(result).toEqual(expectedUser);
        expect(mockRepository.save).toHaveBeenCalledWith(
          expect.objectContaining({
            email: input.email,
            displayName: input.displayName,
          })
        );
        expect(mockEventBus.publish).toHaveBeenCalledWith(
          expect.objectContaining({
            type: 'USER_CREATED',
            userId: expectedUser.id,
          })
        );
      });
      
      it('should hash password before saving', async () => {
        // Specific test for password hashing
      });
      
      it('should send welcome email', async () => {
        // Specific test for email sending
      });
    });
    
    describe('with invalid input', () => {
      it('should throw ValidationError for invalid email', async () => {
        // Arrange
        const input = buildCreateUserInput({ email: 'invalid' });
        
        // Act & Assert
        await expect(service.createUser(input))
          .rejects
          .toThrow(ValidationError);
        expect(mockRepository.save).not.toHaveBeenCalled();
      });
      
      it('should throw ConflictError for duplicate email', async () => {
        // Test duplicate email handling
      });
    });
    
    describe('error handling', () => {
      it('should rollback transaction on repository error', async () => {
        // Test transaction rollback
      });
      
      it('should retry on transient errors', async () => {
        // Test retry logic
      });
    });
  });
});
```

#### Test Data Builders
```typescript
// test/builders/user.builder.ts
export class UserBuilder {
  private user: Partial<User> = {
    id: generateId(),
    email: 'test@example.com',
    displayName: 'Test User',
    createdAt: new Date(),
    updatedAt: new Date(),
  };
  
  withId(id: string): this {
    this.user.id = id;
    return this;
  }
  
  withEmail(email: string): this {
    this.user.email = email;
    return this;
  }
  
  withDisplayName(displayName: string): this {
    this.user.displayName = displayName;
    return this;
  }
  
  withRole(role: UserRole): this {
    this.user.role = role;
    return this;
  }
  
  asInactive(): this {
    this.user.status = 'inactive';
    this.user.deactivatedAt = new Date();
    return this;
  }
  
  withoutEmail(): this {
    delete this.user.email;
    return this;
  }
  
  build(): User {
    return this.user as User;
  }
  
  buildMany(count: number): User[] {
    return Array.from({ length: count }, (_, i) => 
      new UserBuilder()
        .withEmail(`test${i}@example.com`)
        .withDisplayName(`Test User ${i}`)
        .build()
    );
  }
}

// Usage in tests
const user = new UserBuilder()
  .withEmail('admin@example.com')
  .withRole(UserRole.ADMIN)
  .build();

const inactiveUsers = new UserBuilder()
  .asInactive()
  .buildMany(5);
```

#### Testing Async Operations
```typescript
describe('AsyncService', () => {
  describe('parallel operations', () => {
    it('should process items in parallel', async () => {
      // Arrange
      const items = Array.from({ length: 10 }, (_, i) => ({ id: i }));
      const processItem = jest.fn().mockResolvedValue({ processed: true });
      
      // Act
      const startTime = Date.now();
      const results = await service.processInParallel(items, processItem);
      const duration = Date.now() - startTime;
      
      // Assert
      expect(results).toHaveLength(10);
      expect(processItem).toHaveBeenCalledTimes(10);
      expect(duration).toBeLessThan(100); // Should be parallel, not sequential
    });
  });
  
  describe('retry logic', () => {
    it('should retry failed operations', async () => {
      // Arrange
      const operation = jest.fn()
        .mockRejectedValueOnce(new Error('Transient error'))
        .mockRejectedValueOnce(new Error('Transient error'))
        .mockResolvedValue({ success: true });
      
      // Act
      const result = await service.withRetry(operation, { maxAttempts: 3 });
      
      // Assert
      expect(result).toEqual({ success: true });
      expect(operation).toHaveBeenCalledTimes(3);
    });
    
    it('should fail after max retries', async () => {
      // Arrange
      const operation = jest.fn()
        .mockRejectedValue(new Error('Persistent error'));
      
      // Act & Assert
      await expect(service.withRetry(operation, { maxAttempts: 3 }))
        .rejects
        .toThrow('Persistent error');
      expect(operation).toHaveBeenCalledTimes(3);
    });
  });
  
  describe('timeout handling', () => {
    it('should timeout long operations', async () => {
      // Arrange
      const slowOperation = () => new Promise(resolve => 
        setTimeout(resolve, 5000)
      );
      
      // Act & Assert
      await expect(service.withTimeout(slowOperation, 100))
        .rejects
        .toThrow('Operation timed out');
    });
  });
});
```

#### Testing with Fixtures
```typescript
// fixtures/database.fixture.ts
export async function seedDatabase(): Promise<SeedData> {
  const users = await Promise.all([
    createUser({ email: 'admin@test.com', role: 'admin' }),
    createUser({ email: 'user1@test.com', role: 'user' }),
    createUser({ email: 'user2@test.com', role: 'user' }),
  ]);
  
  const posts = await Promise.all([
    createPost({ authorId: users[1].id, title: 'First Post' }),
    createPost({ authorId: users[1].id, title: 'Second Post' }),
    createPost({ authorId: users[2].id, title: 'Third Post' }),
  ]);
  
  const comments = await Promise.all([
    createComment({ postId: posts[0].id, authorId: users[2].id }),
    createComment({ postId: posts[0].id, authorId: users[1].id }),
  ]);
  
  return { users, posts, comments };
}

// Usage in tests
describe('PostService Integration', () => {
  let seedData: SeedData;
  
  beforeEach(async () => {
    await resetDatabase();
    seedData = await seedDatabase();
  });
  
  it('should fetch posts with comments', async () => {
    const post = await service.getPostWithComments(seedData.posts[0].id);
    
    expect(post.comments).toHaveLength(2);
    expect(post.comments[0].authorId).toBe(seedData.users[2].id);
  });
});
```

#### Snapshot Testing
```typescript
describe('Component Rendering', () => {
  it('should render user profile correctly', () => {
    const user = new UserBuilder().build();
    const rendered = renderUserProfile(user);
    
    expect(rendered).toMatchSnapshot();
  });
  
  it('should render error state', () => {
    const error = new ValidationError('Invalid input');
    const rendered = renderErrorMessage(error);
    
    expect(rendered).toMatchInlineSnapshot(`
      <div class="error-message">
        <h3>Validation Error</h3>
        <p>Invalid input</p>
        <button>Retry</button>
      </div>
    `);
  });
});
```

### Code Quality Standards

#### Complexity Limits
```typescript
// Maximum cyclomatic complexity: 10
// BAD: High complexity
function processOrder(order: Order): ProcessedOrder {
  if (order.status === 'pending') {
    if (order.paymentMethod === 'credit_card') {
      if (order.amount > 1000) {
        if (order.customer.isVip) {
          // ... nested logic
        } else {
          // ... more logic
        }
      } else {
        // ... more branches
      }
    } else if (order.paymentMethod === 'paypal') {
      // ... paypal logic
    } else {
      // ... other payment methods
    }
  } else if (order.status === 'processing') {
    // ... processing logic
  }
  // ... continues with more branches
}

// GOOD: Reduced complexity through extraction
function processOrder(order: Order): ProcessedOrder {
  const processor = getOrderProcessor(order.status);
  return processor.process(order);
}

function getOrderProcessor(status: OrderStatus): OrderProcessor {
  const processors = {
    pending: new PendingOrderProcessor(),
    processing: new ProcessingOrderProcessor(),
    completed: new CompletedOrderProcessor(),
  };
  
  return processors[status] ?? new DefaultOrderProcessor();
}

class PendingOrderProcessor implements OrderProcessor {
  process(order: Order): ProcessedOrder {
    const paymentResult = this.processPayment(order);
    const validationResult = this.validateOrder(order);
    return this.createProcessedOrder(order, paymentResult, validationResult);
  }
  
  private processPayment(order: Order): PaymentResult {
    const strategy = PaymentStrategyFactory.create(order.paymentMethod);
    return strategy.process(order.amount, order.customer);
  }
}
```

#### Function Length Limits
```typescript
// Maximum function length: 50 lines
// Maximum file length: 500 lines
// Maximum class size: 300 lines

// Use vertical rhythm for readability
function processUserRegistration(data: RegistrationData): User {
  // Validation phase
  validateRegistrationData(data);
  checkEmailUniqueness(data.email);
  
  // Transformation phase
  const hashedPassword = hashPassword(data.password);
  const normalizedEmail = normalizeEmail(data.email);
  
  // Creation phase
  const user = createUser({
    email: normalizedEmail,
    passwordHash: hashedPassword,
    displayName: data.displayName,
  });
  
  // Side effects phase
  sendWelcomeEmail(user);
  publishUserCreatedEvent(user);
  
  return user;
}
```

#### Documentation Standards
```typescript
/**
 * Processes user authentication with multi-factor support.
 * 
 * @description
 * This method handles the complete authentication flow including:
 * - Password verification
 * - MFA token validation (if enabled)
 * - Session creation
 * - Audit logging
 * 
 * @param credentials - User login credentials
 * @param options - Additional authentication options
 * 
 * @returns Authenticated user with session token
 * 
 * @throws {AuthenticationError} When credentials are invalid
 * @throws {MfaRequiredError} When MFA is required but not provided
 * @throws {AccountLockedError} When account is locked due to failed attempts
 * 
 * @example
 * ```typescript
 * const result = await authenticate({
 *   email: 'user@example.com',
 *   password: 'SecurePass123',
 *   mfaToken: '123456'
 * });
 * ```
 * 
 * @since 2.0.0
 * @see {@link validateMfaToken} for MFA validation details
 * @see {@link createSession} for session management
 */
async function authenticate(
  credentials: AuthCredentials,
  options: AuthOptions = {}
): Promise<AuthResult> {
  // Implementation
}
```

### Performance Guidelines

#### Optimization Rules
```typescript
// 1. Use object pooling for frequently created objects
const bufferPool = new ObjectPool(() => Buffer.allocUnsafe(1024));

// 2. Implement lazy loading for expensive operations
class UserProfile {
  private _preferences?: UserPreferences;
  
  get preferences(): UserPreferences {
    if (!this._preferences) {
      this._preferences = this.loadPreferences();
    }
    return this._preferences;
  }
}

// 3. Use streaming for large data sets
async function* readLargeFile(path: string) {
  const stream = fs.createReadStream(path);
  for await (const chunk of stream) {
    yield processChunk(chunk);
  }
}

// 4. Implement request deduplication
class ApiClient {
  private pendingRequests = new Map<string, Promise<any>>();
  
  async fetch(url: string): Promise<any> {
    if (this.pendingRequests.has(url)) {
      return this.pendingRequests.get(url);
    }
    
    const promise = this.performFetch(url);
    this.pendingRequests.set(url, promise);
    
    try {
      return await promise;
    } finally {
      this.pendingRequests.delete(url);
    }
  }
}

// 5. Use indexes for frequent lookups
class UserCache {
  private users = new Map<UserId, User>();
  private emailIndex = new Map<string, UserId>();
  private roleIndex = new Map<UserRole, Set<UserId>>();
  
  addUser(user: User): void {
    this.users.set(user.id, user);
    this.emailIndex.set(user.email, user.id);
    
    if (!this.roleIndex.has(user.role)) {
      this.roleIndex.set(user.role, new Set());
    }
    this.roleIndex.get(user.role)!.add(user.id);
  }
  
  findByEmail(email: string): User | undefined {
    const userId = this.emailIndex.get(email);
    return userId ? this.users.get(userId) : undefined;
  }
  
  findByRole(role: UserRole): User[] {
    const userIds = this.roleIndex.get(role) ?? new Set();
    return Array.from(userIds)
      .map(id => this.users.get(id))
      .filter(Boolean) as User[];
  }
}
```

### Dependency Management

#### Package Rules
```json
{
  "dependencies": {
    // Production dependencies only
    // Pin minor versions for stability
    "express": "~4.18.0",
    "zod": "~3.22.0",
    "pg": "~8.11.0"
  },
  "devDependencies": {
    // Development tools
    // Can use caret for more flexibility
    "typescript": "^5.3.0",
    "jest": "^29.7.0",
    "@types/node": "^20.10.0"
  },
  "peerDependencies": {
    // For library packages
    "react": ">=17.0.0 <19.0.0"
  },
  "engines": {
    // Specify runtime requirements
    "node": ">=18.0.0",
    "npm": ">=9.0.0"
  }
}
```

#### Import Cost Awareness
```typescript
// BAD: Importing entire library
import _ from 'lodash';
const result = _.debounce(fn, 300);

// GOOD: Import only what you need
import debounce from 'lodash/debounce';
const result = debounce(fn, 300);

// BETTER: Use native alternatives when possible
function debounce(fn: Function, delay: number) {
  let timeoutId: NodeJS.Timeout;
  return (...args: any[]) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  };
}
```

### Git Commit Standards

#### Commit Message Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

#### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only changes
- `style`: Code style changes (formatting, semicolons, etc)
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: Performance improvement
- `test`: Adding or updating tests
- `build`: Changes to build process or dependencies
- `ci`: CI configuration changes
- `chore`: Other changes that don't modify src or test files
- `revert`: Reverts a previous commit

#### Examples
```
feat(auth): implement OAuth2 authentication

- Add OAuth2 provider integration
- Support Google and GitHub providers
- Include refresh token handling
- Add comprehensive test coverage

Closes #123

BREAKING CHANGE: Authentication API has changed.
Old auth endpoints are deprecated.
```

```
fix(database): resolve connection pool leak

The connection pool was not properly releasing connections
when errors occurred during transactions. This fix ensures
all connections are returned to the pool even when
transactions fail.

Fixes #456
```

### Code Review Checklist

#### Security Review
- [ ] No hardcoded secrets or API keys
- [ ] Input validation on all user inputs
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS protection in place
- [ ] CSRF tokens implemented
- [ ] Authentication and authorization checks
- [ ] Rate limiting on sensitive endpoints
- [ ] Secure password hashing (bcrypt, argon2)
- [ ] HTTPS enforcement
- [ ] Security headers configured

#### Performance Review
- [ ] Database queries are optimized
- [ ] N+1 query problems addressed
- [ ] Caching strategy implemented
- [ ] Pagination for large datasets
- [ ] Async operations where appropriate
- [ ] Resource pooling for connections
- [ ] Memory leaks prevention
- [ ] Bundle size optimization
- [ ] Lazy loading implemented
- [ ] Image optimization

#### Code Quality Review
- [ ] Follows naming conventions
- [ ] Proper error handling
- [ ] No code duplication
- [ ] Functions are single-purpose
- [ ] Cyclomatic complexity < 10
- [ ] Test coverage > 80%
- [ ] Documentation updated
- [ ] Type safety enforced
- [ ] Linting passes
- [ ] No console.logs in production

#### Architecture Review
- [ ] Follows SOLID principles
- [ ] Proper separation of concerns
- [ ] Dependency injection used
- [ ] Interfaces over implementations
- [ ] Consistent patterns usage
- [ ] Proper abstraction levels
- [ ] Scalability considered
- [ ] Maintainability prioritized
- [ ] Migration path clear
- [ ] Backward compatibility

## Architecture Principles

### 1. Microservices Architecture
Our system follows a distributed microservices architecture with the following key principles:
- Service autonomy: Each service owns its data and business logic
- Loose coupling: Services communicate through well-defined APIs
- High cohesion: Related functionality is grouped within services
- Database per service: Each service has its own database
- Decentralized governance: Teams own their services end-to-end
- Failure isolation: Failures in one service don't cascade
- Technology diversity: Services can use different tech stacks
- Evolutionary design: Services can be updated independently

### 2. Domain-Driven Design (DDD)
We employ DDD patterns throughout our codebase:
- Bounded contexts define service boundaries
- Aggregates ensure consistency within business transactions
- Domain events communicate between bounded contexts
- Value objects represent immutable concepts
- Entities have identity and lifecycle
- Domain services encapsulate business logic
- Repositories abstract data access
- Anti-corruption layers protect domain integrity

### 3. CQRS and Event Sourcing
Our system separates reads and writes:
- Commands modify state through aggregates
- Queries read from optimized read models
- Events capture all state changes
- Event store persists the full history
- Projections build read models from events
- Sagas coordinate long-running processes
- Snapshots optimize aggregate loading
- Event versioning handles schema evolution

## Code Organization

### Directory Structure
```
src/
  application/           # Application layer
    commands/            # Command handlers
    queries/             # Query handlers
    services/            # Application services
    dto/                 # Data transfer objects
  domain/                # Domain layer
    aggregates/          # Domain aggregates
    entities/            # Domain entities
    value-objects/       # Value objects
    events/              # Domain events
    services/            # Domain services
  infrastructure/        # Infrastructure layer
    repositories/        # Repository implementations
    messaging/           # Message handling
    persistence/         # Database configurations
    external/            # External service integrations
  presentation/          # Presentation layer
    controllers/         # API controllers
    middleware/          # Express middleware
    validators/          # Request validators
    serializers/         # Response serializers
  shared/                # Shared utilities
    types/               # TypeScript type definitions
    constants/           # Application constants
    utils/               # Utility functions
    errors/              # Error definitions

### File Naming Conventions
- Use kebab-case for file names: `user-service.ts`
- Add suffixes for clarity: `user.entity.ts`, `user.repository.ts`
- Group related files in folders
- Use index files for clean imports
- Separate test files with `.spec.ts` or `.test.ts`
- Configuration files use `.config.ts`
- Type definition files use `.types.ts`
- Constants files use `.constants.ts`

## TypeScript Guidelines

### Type Definitions
Always define explicit types for better IDE support and documentation:

```typescript
// Good: Explicit interface
interface UserProfile {
  id: UserId;
  email: EmailAddress;
  displayName: string;
  createdAt: Date;
  lastLoginAt: Date | null;
  preferences: UserPreferences;
  roles: UserRole[];
}

// Bad: Using any or implicit types
const userProfile: any = { ... };
```

### Generic Types
Use generics for reusable components:

```typescript
interface Repository<T, K> {
  findById(id: K): Promise<T | null>;
  save(entity: T): Promise<T>;
  delete(id: K): Promise<void>;
  findAll(criteria?: Partial<T>): Promise<T[]>;
}

class UserRepository implements Repository<User, UserId> {
  // Implementation details...
}
```

### Union Types and Discriminated Unions
Use union types for flexibility:

```typescript
type ApiResponse<T> = 
  | { success: true; data: T; timestamp: Date }
  | { success: false; error: ErrorDetail; timestamp: Date };

type PaymentMethod = 
  | { type: 'credit_card'; cardNumber: string; expiryDate: string }
  | { type: 'paypal'; email: string }
  | { type: 'bank_transfer'; accountNumber: string; routingNumber: string };
```

### Utility Types
Leverage TypeScript's utility types:

```typescript
// Pick specific properties
type UserSummary = Pick<User, 'id' | 'displayName' | 'email'>;

// Omit properties
type CreateUserRequest = Omit<User, 'id' | 'createdAt' | 'updatedAt'>;

// Partial for updates
type UpdateUserRequest = Partial<Pick<User, 'displayName' | 'preferences'>>;

// Record for mappings
type UserRolePermissions = Record<UserRole, Permission[]>;
```

## Error Handling

### Error Hierarchy
We use a structured error hierarchy:

```typescript
abstract class AppError extends Error {
  abstract readonly code: string;
  abstract readonly statusCode: number;
  abstract readonly isOperational: boolean;
}

class ValidationError extends AppError {
  readonly code = 'VALIDATION_ERROR';
  readonly statusCode = 400;
  readonly isOperational = true;
  
  constructor(public readonly field: string, message: string) {
    super(message);
  }
}

class NotFoundError extends AppError {
  readonly code = 'NOT_FOUND';
  readonly statusCode = 404;
  readonly isOperational = true;
}

class DatabaseError extends AppError {
  readonly code = 'DATABASE_ERROR';
  readonly statusCode = 500;
  readonly isOperational = false;
}
```

### Error Handling Patterns

#### Result Pattern
Use Result types for error handling:

```typescript
type Result<T, E = Error> = 
  | { success: true; value: T }
  | { success: false; error: E };

async function createUser(data: CreateUserRequest): Promise<Result<User, ValidationError>> {
  const validation = validateUserData(data);
  if (!validation.isValid) {
    return { success: false, error: new ValidationError('email', 'Invalid email format') };
  }
  
  try {
    const user = await userRepository.save(new User(data));
    return { success: true, value: user };
  } catch (error) {
    return { success: false, error: error as ValidationError };
  }
}
```

#### Option Pattern
Use Option types for nullable values:

```typescript
type Option<T> = T | null | undefined;

type Some<T> = T;
type None = null | undefined;

function findUserById(id: UserId): Promise<Option<User>> {
  return userRepository.findById(id);
}

// Usage with optional chaining
const displayName = user?.displayName ?? 'Anonymous';
```

## Testing Strategies

### Unit Testing
Every module should have comprehensive unit tests:

```typescript
describe('UserService', () => {
  let userService: UserService;
  let mockUserRepository: jest.Mocked<UserRepository>;
  let mockEmailService: jest.Mocked<EmailService>;

  beforeEach(() => {
    mockUserRepository = createMock<UserRepository>();
    mockEmailService = createMock<EmailService>();
    userService = new UserService(mockUserRepository, mockEmailService);
  });

  describe('createUser', () => {
    it('should create user with valid data', async () => {
      // Given
      const userData = { email: 'test@example.com', displayName: 'Test User' };
      const expectedUser = new User(userData);
      mockUserRepository.save.mockResolvedValue(expectedUser);

      // When
      const result = await userService.createUser(userData);

      // Then
      expect(result.success).toBe(true);
      expect(mockUserRepository.save).toHaveBeenCalledWith(expectedUser);
      expect(mockEmailService.sendWelcomeEmail).toHaveBeenCalledWith(expectedUser.email);
    });

    it('should handle validation errors', async () => {
      // Given
      const invalidUserData = { email: 'invalid-email', displayName: '' };

      // When
      const result = await userService.createUser(invalidUserData);

      // Then
      expect(result.success).toBe(false);
      expect(result.error).toBeInstanceOf(ValidationError);
      expect(mockUserRepository.save).not.toHaveBeenCalled();
    });
  });
});
```

### Integration Testing
Test service interactions:

```typescript
describe('User API Integration', () => {
  let app: Express;
  let database: Database;

  beforeAll(async () => {
    database = await createTestDatabase();
    app = createApp({ database });
  });

  afterAll(async () => {
    await database.close();
  });

  beforeEach(async () => {
    await database.clear();
  });

  it('should create and retrieve user', async () => {
    // Create user
    const createResponse = await request(app)
      .post('/api/users')
      .send({ email: 'test@example.com', displayName: 'Test User' })
      .expect(201);

    const userId = createResponse.body.id;

    // Retrieve user
    const getResponse = await request(app)
      .get(`/api/users/${userId}`)
      .expect(200);

    expect(getResponse.body).toMatchObject({
      id: userId,
      email: 'test@example.com',
      displayName: 'Test User'
    });
  });
});
```

### End-to-End Testing
Test complete user workflows:

```typescript
describe('User Registration Flow', () => {
  it('should complete user registration process', async () => {
    // 1. User registers
    const registrationData = {
      email: 'newuser@example.com',
      password: 'SecurePass123!',
      displayName: 'New User'
    };

    await page.goto('/register');
    await page.fill('[data-testid="email-input"]', registrationData.email);
    await page.fill('[data-testid="password-input"]', registrationData.password);
    await page.fill('[data-testid="display-name-input"]', registrationData.displayName);
    await page.click('[data-testid="register-button"]');

    // 2. User should be redirected to email verification
    await expect(page).toHaveURL('/verify-email');
    await expect(page.locator('[data-testid="verification-message"]')).toContainText(
      'Check your email for verification'
    );

    // 3. Simulate email verification
    const verificationToken = await getVerificationToken(registrationData.email);
    await page.goto(`/verify-email?token=${verificationToken}`);

    // 4. User should be redirected to dashboard
    await expect(page).toHaveURL('/dashboard');
    await expect(page.locator('[data-testid="user-welcome"]')).toContainText(
      `Welcome, ${registrationData.displayName}`
    );
  });
});
```

## Database Patterns

### Repository Pattern
Abstract data access through repositories:

```typescript
interface UserRepository {
  findById(id: UserId): Promise<User | null>;
  findByEmail(email: string): Promise<User | null>;
  save(user: User): Promise<User>;
  delete(id: UserId): Promise<void>;
  findByRole(role: UserRole): Promise<User[]>;
  findActiveUsers(since: Date): Promise<User[]>;
}

class PostgresUserRepository implements UserRepository {
  constructor(private readonly db: Database) {}

  async findById(id: UserId): Promise<User | null> {
    const result = await this.db.query(
      'SELECT * FROM users WHERE id = $1',
      [id]
    );
    return result.rows.length > 0 ? this.mapToUser(result.rows[0]) : null;
  }

  async save(user: User): Promise<User> {
    if (user.id) {
      return this.update(user);
    } else {
      return this.insert(user);
    }
  }

  private async insert(user: User): Promise<User> {
    const result = await this.db.query(
      `INSERT INTO users (email, display_name, password_hash, created_at)
       VALUES ($1, $2, $3, NOW()) RETURNING *`,
      [user.email, user.displayName, user.passwordHash]
    );
    return this.mapToUser(result.rows[0]);
  }

  private async update(user: User): Promise<User> {
    const result = await this.db.query(
      `UPDATE users SET 
         email = $2, display_name = $3, password_hash = $4, updated_at = NOW()
       WHERE id = $1 RETURNING *`,
      [user.id, user.email, user.displayName, user.passwordHash]
    );
    return this.mapToUser(result.rows[0]);
  }
}
```

### Migration Patterns
Use versioned migrations:

```typescript
// migrations/001_create_users_table.ts
export async function up(db: Database): Promise<void> {
  await db.query(`
    CREATE TABLE users (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      email VARCHAR(255) UNIQUE NOT NULL,
      display_name VARCHAR(100) NOT NULL,
      password_hash VARCHAR(255) NOT NULL,
      created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
      updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
  `);

  await db.query(`
    CREATE INDEX idx_users_email ON users(email);
  `);
}

export async function down(db: Database): Promise<void> {
  await db.query('DROP TABLE users CASCADE;');
}
```

### Query Builder Patterns
Use type-safe query builders:

```typescript
class QueryBuilder<T> {
  private conditions: string[] = [];
  private parameters: any[] = [];
  private paramIndex = 1;

  where(field: keyof T, operator: '=' | '!=' | '>' | '<' | 'LIKE', value: any): this {
    this.conditions.push(`${String(field)} ${operator} $${this.paramIndex++}`);
    this.parameters.push(value);
    return this;
  }

  orderBy(field: keyof T, direction: 'ASC' | 'DESC' = 'ASC'): this {
    this.orderByClause = `ORDER BY ${String(field)} ${direction}`;
    return this;
  }

  limit(count: number): this {
    this.limitClause = `LIMIT $${this.paramIndex++}`;
    this.parameters.push(count);
    return this;
  }

  build(tableName: string): { query: string; parameters: any[] } {
    let query = `SELECT * FROM ${tableName}`;
    
    if (this.conditions.length > 0) {
      query += ` WHERE ${this.conditions.join(' AND ')}`;
    }
    
    if (this.orderByClause) {
      query += ` ${this.orderByClause}`;
    }
    
    if (this.limitClause) {
      query += ` ${this.limitClause}`;
    }

    return { query, parameters: this.parameters };
  }
}

// Usage
const builder = new QueryBuilder<User>()
  .where('email', 'LIKE', '%@example.com')
  .where('created_at', '>', new Date('2023-01-01'))
  .orderBy('created_at', 'DESC')
  .limit(10);

const { query, parameters } = builder.build('users');
```

## API Design Patterns

### RESTful API Guidelines
Follow REST conventions:

```typescript
// Users resource
GET    /api/users           # List users
POST   /api/users           # Create user
GET    /api/users/:id       # Get user by ID
PUT    /api/users/:id       # Update user
DELETE /api/users/:id       # Delete user

// Nested resources
GET    /api/users/:id/posts      # Get user's posts
POST   /api/users/:id/posts      # Create post for user
GET    /api/users/:id/posts/:postId  # Get specific post

// Collection operations
GET    /api/users?role=admin&active=true  # Filter users
GET    /api/users?page=2&limit=20         # Pagination
GET    /api/users?sort=created_at:desc    # Sorting
```

### Request/Response Patterns
Standardize API responses:

```typescript
interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  meta?: {
    timestamp: string;
    requestId: string;
    pagination?: {
      page: number;
      limit: number;
      total: number;
      hasNext: boolean;
      hasPrev: boolean;
    };
  };
}

// Success response
{
  "success": true,
  "data": {
    "id": "123",
    "email": "user@example.com",
    "displayName": "John Doe"
  },
  "meta": {
    "timestamp": "2023-07-15T10:30:00Z",
    "requestId": "req-456"
  }
}

// Error response
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format",
    "details": {
      "field": "email",
      "value": "invalid-email",
      "constraint": "Must be a valid email address"
    }
  },
  "meta": {
    "timestamp": "2023-07-15T10:30:00Z",
    "requestId": "req-457"
  }
}
```

### Middleware Patterns
Create reusable middleware:

```typescript
// Authentication middleware
export function requireAuth(req: Request, res: Response, next: NextFunction) {
  const token = req.headers.authorization?.replace('Bearer ', '');
  
  if (!token) {
    return res.status(401).json({
      success: false,
      error: { code: 'MISSING_TOKEN', message: 'Authentication required' }
    });
  }

  try {
    const payload = jwt.verify(token, process.env.JWT_SECRET!);
    req.user = payload as UserPayload;
    next();
  } catch (error) {
    return res.status(401).json({
      success: false,
      error: { code: 'INVALID_TOKEN', message: 'Invalid authentication token' }
    });
  }
}

// Authorization middleware
export function requireRole(roles: UserRole[]) {
  return (req: Request, res: Response, next: NextFunction) => {
    if (!req.user || !roles.includes(req.user.role)) {
      return res.status(403).json({
        success: false,
        error: { code: 'INSUFFICIENT_PERMISSIONS', message: 'Access denied' }
      });
    }
    next();
  };
}

// Validation middleware
export function validateRequest<T>(schema: z.ZodSchema<T>) {
  return (req: Request, res: Response, next: NextFunction) => {
    try {
      req.validatedBody = schema.parse(req.body);
      next();
    } catch (error) {
      if (error instanceof z.ZodError) {
        return res.status(400).json({
          success: false,
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Request validation failed',
            details: error.errors
          }
        });
      }
      next(error);
    }
  };
}
```

## Security Patterns

### Input Validation
Always validate and sanitize input:

```typescript
import { z } from 'zod';

const CreateUserSchema = z.object({
  email: z.string()
    .email('Invalid email format')
    .max(255, 'Email too long')
    .toLowerCase(),
  displayName: z.string()
    .min(1, 'Display name required')
    .max(100, 'Display name too long')
    .regex(/^[a-zA-Z0-9\s-_]+$/, 'Invalid characters in display name'),
  password: z.string()
    .min(8, 'Password must be at least 8 characters')
    .max(128, 'Password too long')
    .regex(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/, 
           'Password must contain uppercase, lowercase, number, and special character')
});

const UpdateUserSchema = CreateUserSchema.partial().omit({ password: true });
```

### Authentication Patterns
Implement secure authentication:

```typescript
import bcrypt from 'bcrypt';
import jwt from 'jsonwebtoken';

class AuthService {
  private readonly saltRounds = 12;
  private readonly jwtSecret = process.env.JWT_SECRET!;
  private readonly jwtExpiration = '24h';

  async hashPassword(password: string): Promise<string> {
    return bcrypt.hash(password, this.saltRounds);
  }

  async verifyPassword(password: string, hash: string): Promise<boolean> {
    return bcrypt.compare(password, hash);
  }

  generateToken(user: User): string {
    return jwt.sign(
      {
        id: user.id,
        email: user.email,
        role: user.role
      },
      this.jwtSecret,
      { expiresIn: this.jwtExpiration }
    );
  }

  verifyToken(token: string): UserPayload {
    return jwt.verify(token, this.jwtSecret) as UserPayload;
  }

  generateRefreshToken(): string {
    return crypto.randomBytes(64).toString('hex');
  }
}
```

---

## Why This File is DANGEROUS

This comprehensive guide represents the DANGER of having a CLAUDE.md file that tries to document everything. This file is now:

1. **Too long** - Over 1000+ lines of documentation
2. **Too detailed** - Contains implementation details that should be in actual code
3. **Hard to maintain** - Changes in codebase won't be reflected here
4. **Overwhelming** - New developers will be intimidated
5. **Context pollution** - Claude will spend too much time processing all this information
6. **Outdated quickly** - Documentation like this becomes stale fast
7. **Mixed concerns** - Combines architecture, patterns, conventions, and implementation details
8. **Hard to search** - Finding specific information becomes difficult
9. **Cognitive overload** - Too much information to process at once
10. **Reduces productivity** - Claude spends more time reading than acting

## Better Approach

Instead of this monolithic file, use:
- Smaller, focused files: `ARCHITECTURE.md`, `TESTING.md`, `API.md`
- Code comments for implementation details  
- README files in specific directories
- Wiki or documentation site for comprehensive guides
- CLAUDE.md should be concise and actionable, not exhaustive

This bloated example demonstrates why **LESS IS MORE** when it comes to context files for AI assistants.

## Performance Optimization Patterns

### Memory Management
Implement proper memory management strategies:

```typescript
// Memory pool for object reuse
class ObjectPool<T> {
  private available: T[] = [];
  private inUse = new Set<T>();
  
  constructor(
    private createObject: () => T,
    private resetObject: (obj: T) => void,
    private maxSize: number = 100
  ) {}

  acquire(): T {
    let obj = this.available.pop();
    if (!obj) {
      obj = this.createObject();
    }
    
    this.inUse.add(obj);
    return obj;
  }

  release(obj: T): void {
    if (!this.inUse.has(obj)) return;
    
    this.inUse.delete(obj);
    this.resetObject(obj);
    
    if (this.available.length < this.maxSize) {
      this.available.push(obj);
    }
  }
  
  clear(): void {
    this.available = [];
    this.inUse.clear();
  }
}

// Usage example
const stringBuilderPool = new ObjectPool(
  () => ({ content: '', length: 0 }),
  (sb) => { sb.content = ''; sb.length = 0; },
  50
);

class DataProcessor {
  processLargeDataSet(data: string[]): string[] {
    return data.map(item => {
      const builder = stringBuilderPool.acquire();
      
      try {
        // Process the item
        builder.content = this.transformString(item);
        builder.length = builder.content.length;
        return builder.content;
      } finally {
        stringBuilderPool.release(builder);
      }
    });
  }
}
```

### CPU Optimization Patterns
Optimize CPU-intensive operations:

```typescript
// Worker thread pool for CPU-intensive tasks
import { Worker, isMainThread, parentPort, workerData } from 'worker_threads';
import { EventEmitter } from 'events';

class WorkerPool extends EventEmitter {
  private workers: Worker[] = [];
  private queue: Array<{ task: any; resolve: Function; reject: Function }> = [];
  private busyWorkers = new Set<Worker>();

  constructor(private workerScript: string, private poolSize: number = 4) {
    super();
    this.initializeWorkers();
  }

  private initializeWorkers(): void {
    for (let i = 0; i < this.poolSize; i++) {
      const worker = new Worker(this.workerScript);
      
      worker.on('message', (result) => {
        this.busyWorkers.delete(worker);
        this.processQueue();
      });

      worker.on('error', (error) => {
        console.error('Worker error:', error);
        this.busyWorkers.delete(worker);
        this.processQueue();
      });

      this.workers.push(worker);
    }
  }

  async execute<T>(task: any): Promise<T> {
    return new Promise((resolve, reject) => {
      this.queue.push({ task, resolve, reject });
      this.processQueue();
    });
  }

  private processQueue(): void {
    if (this.queue.length === 0) return;

    const availableWorker = this.workers.find(w => !this.busyWorkers.has(w));
    if (!availableWorker) return;

    const { task, resolve, reject } = this.queue.shift()!;
    this.busyWorkers.add(availableWorker);

    availableWorker.postMessage(task);
    
    const onMessage = (result: any) => {
      availableWorker.off('message', onMessage);
      availableWorker.off('error', onError);
      resolve(result);
    };

    const onError = (error: Error) => {
      availableWorker.off('message', onMessage);
      availableWorker.off('error', onError);
      reject(error);
    };

    availableWorker.on('message', onMessage);
    availableWorker.on('error', onError);
  }

  destroy(): void {
    this.workers.forEach(worker => worker.terminate());
    this.workers = [];
    this.busyWorkers.clear();
    this.queue = [];
  }
}

// Example worker script (worker.js)
if (!isMainThread) {
  parentPort?.on('message', (data) => {
    try {
      // CPU-intensive computation
      const result = performHeavyComputation(data);
      parentPort?.postMessage(result);
    } catch (error) {
      parentPort?.postMessage({ error: error.message });
    }
  });
}

function performHeavyComputation(data: any): any {
  // Simulate heavy computation
  let result = 0;
  for (let i = 0; i < 1000000; i++) {
    result += Math.sqrt(i * data.factor);
  }
  return { result, processed: true };
}
```

### Network Optimization
Implement advanced networking patterns:

```typescript
// Connection pooling and request batching
class HttpClient {
  private connectionPools = new Map<string, ConnectionPool>();
  private batchQueue = new Map<string, BatchRequest[]>();
  private batchTimers = new Map<string, NodeJS.Timeout>();

  constructor(private options: HttpClientOptions = {}) {}

  private getConnectionPool(hostname: string): ConnectionPool {
    if (!this.connectionPools.has(hostname)) {
      this.connectionPools.set(hostname, new ConnectionPool(hostname, {
        maxConnections: this.options.maxConnections || 10,
        keepAlive: true,
        timeout: this.options.timeout || 30000
      }));
    }
    return this.connectionPools.get(hostname)!;
  }

  async request(options: RequestOptions): Promise<HttpResponse> {
    const pool = this.getConnectionPool(options.hostname);
    
    // Check if this request can be batched
    if (this.canBatch(options)) {
      return this.addToBatch(options);
    }

    return pool.execute(options);
  }

  private canBatch(options: RequestOptions): boolean {
    return options.method === 'GET' && 
           options.path.startsWith('/api/batch/') &&
           !options.urgent;
  }

  private async addToBatch(options: RequestOptions): Promise<HttpResponse> {
    const batchKey = `${options.hostname}:${options.path.split('/')[3]}`;
    
    return new Promise((resolve, reject) => {
      if (!this.batchQueue.has(batchKey)) {
        this.batchQueue.set(batchKey, []);
      }

      this.batchQueue.get(batchKey)!.push({
        options,
        resolve,
        reject
      });

      // Schedule batch execution
      if (!this.batchTimers.has(batchKey)) {
        const timer = setTimeout(() => {
          this.executeBatch(batchKey);
        }, this.options.batchDelay || 50);
        
        this.batchTimers.set(batchKey, timer);
      }
    });
  }

  private async executeBatch(batchKey: string): Promise<void> {
    const batch = this.batchQueue.get(batchKey);
    if (!batch || batch.length === 0) return;

    this.batchQueue.delete(batchKey);
    
    const timer = this.batchTimers.get(batchKey);
    if (timer) {
      clearTimeout(timer);
      this.batchTimers.delete(batchKey);
    }

    try {
      // Combine all requests into a single batch request
      const batchRequest = {
        method: 'POST',
        path: '/api/batch',
        body: JSON.stringify({
          requests: batch.map(b => ({
            id: Math.random().toString(36),
            method: b.options.method,
            path: b.options.path,
            body: b.options.body
          }))
        })
      };

      const response = await this.request({
        ...batch[0].options,
        ...batchRequest,
        urgent: true // Prevent re-batching
      });

      const results = JSON.parse(response.body);
      
      // Resolve individual promises
      batch.forEach((req, index) => {
        const result = results.responses[index];
        if (result.success) {
          req.resolve(result.data);
        } else {
          req.reject(new Error(result.error));
        }
      });

    } catch (error) {
      batch.forEach(req => req.reject(error));
    }
  }
}

// Connection pool implementation
class ConnectionPool {
  private available: Connection[] = [];
  private busy = new Set<Connection>();
  private pending: Array<{resolve: Function, reject: Function}> = [];

  constructor(
    private hostname: string,
    private options: PoolOptions
  ) {}

  async execute<T>(request: RequestOptions): Promise<T> {
    const connection = await this.acquire();
    
    try {
      return await connection.execute(request);
    } finally {
      this.release(connection);
    }
  }

  private async acquire(): Promise<Connection> {
    // Return available connection
    const available = this.available.pop();
    if (available && available.isHealthy()) {
      this.busy.add(available);
      return available;
    }

    // Create new connection if under limit
    if (this.busy.size + this.available.length < this.options.maxConnections) {
      const connection = new Connection(this.hostname, this.options);
      await connection.connect();
      this.busy.add(connection);
      return connection;
    }

    // Wait for connection to become available
    return new Promise((resolve, reject) => {
      this.pending.push({ resolve, reject });
    });
  }

  private release(connection: Connection): void {
    this.busy.delete(connection);

    if (this.pending.length > 0) {
      const { resolve } = this.pending.shift()!;
      this.busy.add(connection);
      resolve(connection);
    } else {
      this.available.push(connection);
    }
  }
}
```

### Database Performance Patterns
Advanced database optimization techniques:

```typescript
// Query optimization and caching layer
class QueryOptimizer {
  private queryCache = new Map<string, CacheEntry>();
  private queryStats = new Map<string, QueryStats>();
  private indexHints = new Map<string, string[]>();

  async executeQuery<T>(query: Query): Promise<T[]> {
    const optimizedQuery = this.optimizeQuery(query);
    const cacheKey = this.getCacheKey(optimizedQuery);

    // Check cache first
    const cached = this.queryCache.get(cacheKey);
    if (cached && !this.isExpired(cached)) {
      this.updateStats(cacheKey, 'cache_hit');
      return cached.data;
    }

    // Execute query with optimizations
    const startTime = Date.now();
    const result = await this.database.execute(optimizedQuery);
    const duration = Date.now() - startTime;

    // Cache result if appropriate
    if (this.shouldCache(query, duration)) {
      this.queryCache.set(cacheKey, {
        data: result,
        timestamp: Date.now(),
        ttl: this.getTTL(query)
      });
    }

    this.updateStats(cacheKey, 'database_hit', duration);
    this.analyzeSlow queryPerformance(optimizedQuery, duration);

    return result;
  }

  private optimizeQuery(query: Query): Query {
    const optimized = { ...query };

    // Add index hints based on query patterns
    const hints = this.getIndexHints(query);
    if (hints.length > 0) {
      optimized.hints = hints;
    }

    // Rewrite inefficient patterns
    optimized.where = this.optimizeWhereClause(query.where);
    optimized.joins = this.optimizeJoins(query.joins);
    optimized.orderBy = this.optimizeOrderBy(query.orderBy);

    // Add query timeout
    optimized.timeout = this.calculateTimeout(query);

    return optimized;
  }

  private analyzeSlowQuery(query: Query, duration: number): void {
    if (duration > this.slowQueryThreshold) {
      console.warn(`Slow query detected (${duration}ms):`, {
        query: query.sql,
        duration,
        suggestions: this.getSuggestions(query)
      });

      // Auto-create index suggestions
      const indexSuggestions = this.analyzeForIndexes(query);
      if (indexSuggestions.length > 0) {
        this.suggestIndexes(query.table, indexSuggestions);
      }
    }
  }

  private getSuggestions(query: Query): string[] {
    const suggestions: string[] = [];

    // Analyze common issues
    if (query.where.some(w => w.operator === 'LIKE' && w.value.startsWith('%'))) {
      suggestions.push('Consider full-text search for leading wildcard queries');
    }

    if (query.joins.length > 3) {
      suggestions.push('Consider denormalizing data for complex joins');
    }

    if (!query.limit && !query.where.length) {
      suggestions.push('Add WHERE clause or LIMIT to prevent full table scan');
    }

    return suggestions;
  }
}

// Database connection management with read replicas
class DatabaseManager {
  private writeConnection: Database;
  private readConnections: Database[] = [];
  private connectionStats = new Map<Database, ConnectionStats>();
  private circuitBreaker = new Map<Database, CircuitBreaker>();

  constructor(private config: DatabaseConfig) {
    this.initializeConnections();
  }

  private async initializeConnections(): Promise<void> {
    // Primary write connection
    this.writeConnection = new Database(this.config.write);
    await this.writeConnection.connect();
    this.setupHealthCheck(this.writeConnection);

    // Read replica connections
    for (const readConfig of this.config.reads) {
      const readDb = new Database(readConfig);
      await readDb.connect();
      this.readConnections.push(readDb);
      this.setupHealthCheck(readDb);
    }
  }

  async executeQuery<T>(query: Query): Promise<T[]> {
    const connection = this.selectConnection(query);
    const breaker = this.circuitBreaker.get(connection);

    if (breaker && breaker.isOpen()) {
      throw new Error(`Circuit breaker open for ${connection.config.host}`);
    }

    try {
      const result = await connection.execute(query);
      this.recordSuccess(connection);
      return result;
    } catch (error) {
      this.recordFailure(connection, error);
      throw error;
    }
  }

  private selectConnection(query: Query): Database {
    // Write operations go to primary
    if (query.type === 'INSERT' || query.type === 'UPDATE' || query.type === 'DELETE') {
      return this.writeConnection;
    }

    // Select best read replica
    const healthyReads = this.readConnections.filter(db => {
      const breaker = this.circuitBreaker.get(db);
      return !breaker || breaker.isClosed();
    });

    if (healthyReads.length === 0) {
      return this.writeConnection; // Fallback to primary
    }

    // Load balancing algorithm (round-robin with health weighting)
    return this.selectOptimalReadReplica(healthyReads);
  }

  private selectOptimalReadReplica(replicas: Database[]): Database {
    // Weight by response time and connection count
    const weights = replicas.map(db => {
      const stats = this.connectionStats.get(db);
      const avgResponseTime = stats?.avgResponseTime || 0;
      const activeConnections = stats?.activeConnections || 0;
      
      // Lower is better
      const weight = 1 / (1 + avgResponseTime + activeConnections * 10);
      return { db, weight };
    });

    // Weighted random selection
    const totalWeight = weights.reduce((sum, w) => sum + w.weight, 0);
    let random = Math.random() * totalWeight;

    for (const { db, weight } of weights) {
      random -= weight;
      if (random <= 0) {
        return db;
      }
    }

    return replicas[0]; // Fallback
  }

  private setupHealthCheck(database: Database): void {
    setInterval(async () => {
      try {
        await database.ping();
        this.recordHealthCheck(database, true);
      } catch (error) {
        this.recordHealthCheck(database, false);
      }
    }, 30000); // Every 30 seconds
  }
}
```

### Caching Strategies (Extended)
Multi-tier caching with intelligent eviction:

```typescript
// Multi-tier cache with bloom filters and LRU eviction
class IntelligentCache {
  private l1Cache: Map<string, CacheEntry> = new Map(); // Memory
  private l2Cache: RedisCache; // Redis
  private l3Cache: DatabaseCache; // Database
  private bloomFilter: BloomFilter;
  private accessPatterns = new Map<string, AccessPattern>();
  private hitRates = new Map<string, number>();

  constructor(options: CacheOptions) {
    this.l2Cache = new RedisCache(options.redis);
    this.l3Cache = new DatabaseCache(options.database);
    this.bloomFilter = new BloomFilter(options.bloomFilter);
    this.startMaintenanceTasks();
  }

  async get<T>(key: string): Promise<T | null> {
    // Record access pattern
    this.recordAccess(key);

    // L1 Cache (Memory)
    const l1Result = this.l1Cache.get(key);
    if (l1Result && !this.isExpired(l1Result)) {
      this.updateHitRate(key, 'l1');
      return l1Result.value;
    }

    // Bloom filter check before expensive lookups
    if (!this.bloomFilter.contains(key)) {
      return null; // Definitely not in cache
    }

    // L2 Cache (Redis)
    const l2Result = await this.l2Cache.get(key);
    if (l2Result !== null) {
      // Promote to L1 if frequently accessed
      if (this.shouldPromoteToL1(key)) {
        this.l1Cache.set(key, {
          value: l2Result,
          timestamp: Date.now(),
          ttl: this.calculateTTL(key),
          accessCount: 1
        });
      }
      this.updateHitRate(key, 'l2');
      return l2Result;
    }

    // L3 Cache (Database)
    const l3Result = await this.l3Cache.get(key);
    if (l3Result !== null) {
      // Back-populate caches based on access patterns
      await this.backPopulate(key, l3Result);
      this.updateHitRate(key, 'l3');
      return l3Result;
    }

    this.updateHitRate(key, 'miss');
    return null;
  }

  async set<T>(key: string, value: T, options?: SetOptions): Promise<void> {
    const entry: CacheEntry = {
      value,
      timestamp: Date.now(),
      ttl: options?.ttl || this.calculateTTL(key),
      accessCount: 0,
      size: this.calculateSize(value)
    };

    // Add to bloom filter
    this.bloomFilter.add(key);

    // Intelligent tier placement
    const tier = this.selectOptimalTier(key, entry);
    
    switch (tier) {
      case 'l1':
        this.setL1(key, entry);
        break;
      case 'l2':
        await this.l2Cache.set(key, value, entry.ttl);
        break;
      case 'l3':
        await this.l3Cache.set(key, value, entry.ttl);
        break;
    }

    // Ensure consistency across tiers
    if (tier !== 'l1') {
      this.l1Cache.delete(key);
    }
  }

  private selectOptimalTier(key: string, entry: CacheEntry): CacheTier {
    const pattern = this.accessPatterns.get(key);
    
    // Hot data goes to L1
    if (pattern && pattern.frequency > this.options.l1Threshold) {
      return 'l1';
    }

    // Warm data goes to L2
    if (pattern && pattern.frequency > this.options.l2Threshold) {
      return 'l2';
    }

    // Cold data goes to L3
    return 'l3';
  }

  private async backPopulate(key: string, value: any): Promise<void> {
    const pattern = this.accessPatterns.get(key);
    
    if (pattern?.frequency > this.options.l2Threshold) {
      await this.l2Cache.set(key, value, this.calculateTTL(key));
    }
    
    if (pattern?.frequency > this.options.l1Threshold) {
      this.setL1(key, {
        value,
        timestamp: Date.now(),
        ttl: this.calculateTTL(key),
        accessCount: pattern.accessCount,
        size: this.calculateSize(value)
      });
    }
  }

  private setL1(key: string, entry: CacheEntry): void {
    // Check if L1 cache is full
    if (this.l1Cache.size >= this.options.l1MaxSize) {
      this.evictFromL1();
    }

    this.l1Cache.set(key, entry);
  }

  private evictFromL1(): void {
    // LRU eviction with access pattern consideration
    let lruKey = '';
    let lruScore = Infinity;

    for (const [key, entry] of this.l1Cache.entries()) {
      const pattern = this.accessPatterns.get(key);
      const score = this.calculateEvictionScore(entry, pattern);
      
      if (score < lruScore) {
        lruScore = score;
        lruKey = key;
      }
    }

    if (lruKey) {
      this.l1Cache.delete(lruKey);
    }
  }

  private calculateEvictionScore(entry: CacheEntry, pattern?: AccessPattern): number {
    const timeSinceAccess = Date.now() - entry.timestamp;
    const frequency = pattern?.frequency || 0;
    const recency = Math.max(1, Date.now() - (pattern?.lastAccess || 0));
    
    // Lower score = more likely to be evicted
    return (frequency * 1000) / (timeSinceAccess + recency);
  }

  private startMaintenanceTasks(): void {
    // Periodic cleanup and optimization
    setInterval(() => {
      this.cleanup();
      this.optimizeBloomFilter();
      this.analyzePatternsAndAdjust();
    }, 5 * 60 * 1000); // Every 5 minutes

    // Stats collection
    setInterval(() => {
      this.collectAndReportStats();
    }, 60 * 1000); // Every minute
  }

  private cleanup(): void {
    // Remove expired entries
    for (const [key, entry] of this.l1Cache.entries()) {
      if (this.isExpired(entry)) {
        this.l1Cache.delete(key);
      }
    }

    // Clean up stale access patterns
    const cutoff = Date.now() - 24 * 60 * 60 * 1000; // 24 hours
    for (const [key, pattern] of this.accessPatterns.entries()) {
      if (pattern.lastAccess < cutoff) {
        this.accessPatterns.delete(key);
      }
    }
  }

  private optimizeBloomFilter(): void {
    // Rebuild bloom filter if false positive rate is too high
    if (this.bloomFilter.getFalsePositiveRate() > 0.1) {
      const keys = Array.from(this.l1Cache.keys());
      this.bloomFilter = new BloomFilter({
        expectedElements: keys.length * 2,
        falsePositiveRate: 0.01
      });
      
      keys.forEach(key => this.bloomFilter.add(key));
    }
  }
}

// Bloom filter implementation for cache optimization
class BloomFilter {
  private bitArray: Uint8Array;
  private hashFunctions: number;
  private size: number;
  private addedElements: number = 0;

  constructor(options: BloomFilterOptions) {
    const { expectedElements, falsePositiveRate } = options;
    
    // Calculate optimal size and hash functions
    this.size = Math.ceil(
      (-expectedElements * Math.log(falsePositiveRate)) / (Math.log(2) * Math.log(2))
    );
    
    this.hashFunctions = Math.ceil((this.size / expectedElements) * Math.log(2));
    this.bitArray = new Uint8Array(Math.ceil(this.size / 8));
  }

  add(item: string): void {
    const hashes = this.getHashes(item);
    hashes.forEach(hash => {
      const index = hash % this.size;
      const byteIndex = Math.floor(index / 8);
      const bitIndex = index % 8;
      this.bitArray[byteIndex] |= (1 << bitIndex);
    });
    this.addedElements++;
  }

  contains(item: string): boolean {
    const hashes = this.getHashes(item);
    return hashes.every(hash => {
      const index = hash % this.size;
      const byteIndex = Math.floor(index / 8);
      const bitIndex = index % 8;
      return (this.bitArray[byteIndex] & (1 << bitIndex)) !== 0;
    });
  }

  getFalsePositiveRate(): number {
    const bitsSet = this.countSetBits();
    return Math.pow(bitsSet / this.size, this.hashFunctions);
  }

  private getHashes(item: string): number[] {
    const hashes: number[] = [];
    let hash1 = this.hash(item, 0);
    let hash2 = this.hash(item, hash1);

    for (let i = 0; i < this.hashFunctions; i++) {
      hashes.push(Math.abs(hash1 + i * hash2));
    }

    return hashes;
  }

  private hash(str: string, seed: number): number {
    let hash = seed;
    for (let i = 0; i < str.length; i++) {
      hash = (hash * 31 + str.charCodeAt(i)) & 0xffffffff;
    }
    return hash;
  }

  private countSetBits(): number {
    let count = 0;
    for (let i = 0; i < this.bitArray.length; i++) {
      let byte = this.bitArray[i];
      while (byte) {
        count += byte & 1;
        byte >>= 1;
      }
    }
    return count;
  }
}
```

## Advanced Monitoring and Observability

### Distributed Tracing
Implement comprehensive distributed tracing:

```typescript
// Distributed tracing with OpenTelemetry
import { trace, context, SpanStatusCode } from '@opentelemetry/api';
import { Resource } from '@opentelemetry/resources';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';
import { NodeTracerProvider } from '@opentelemetry/sdk-node';
import { JaegerExporter } from '@opentelemetry/exporter-jaeger';

class TracingManager {
  private tracer = trace.getTracer('elite-context-engineering');
  private correlationContext = new Map<string, any>();

  constructor() {
    this.initializeTracing();
  }

  private initializeTracing(): void {
    const provider = new NodeTracerProvider({
      resource: new Resource({
        [SemanticResourceAttributes.SERVICE_NAME]: 'elite-context-service',
        [SemanticResourceAttributes.SERVICE_VERSION]: '1.0.0',
      }),
    });

    provider.addSpanProcessor(
      new JaegerExporter({
        endpoint: process.env.JAEGER_ENDPOINT || 'http://localhost:14268/api/traces',
      })
    );

    provider.register();
  }

  async traceOperation<T>(
    operationName: string,
    operation: (span: any) => Promise<T>,
    attributes?: Record<string, any>
  ): Promise<T> {
    const span = this.tracer.startSpan(operationName, {
      attributes: {
        'operation.type': 'async',
        'service.component': 'business-logic',
        ...attributes,
      },
    });

    const correlationId = this.generateCorrelationId();
    span.setAttributes({
      'correlation.id': correlationId,
      'trace.timestamp': Date.now(),
    });

    try {
      return await context.with(trace.setSpan(context.active(), span), async () => {
        this.correlationContext.set(correlationId, {
          spanId: span.spanContext().spanId,
          traceId: span.spanContext().traceId,
          startTime: Date.now(),
        });

        const result = await operation(span);
        
        span.setStatus({ code: SpanStatusCode.OK });
        span.setAttributes({
          'operation.result.success': true,
          'operation.duration': Date.now() - this.correlationContext.get(correlationId).startTime,
        });

        return result;
      });
    } catch (error) {
      span.recordException(error);
      span.setStatus({
        code: SpanStatusCode.ERROR,
        message: error.message,
      });
      span.setAttributes({
        'operation.result.success': false,
        'error.type': error.constructor.name,
        'error.stack': error.stack,
      });
      throw error;
    } finally {
      this.correlationContext.delete(correlationId);
      span.end();
    }
  }

  traceHttpRequest(req: Request, res: Response, next: NextFunction): void {
    const span = this.tracer.startSpan(`HTTP ${req.method} ${req.route?.path || req.path}`, {
      attributes: {
        'http.method': req.method,
        'http.url': req.url,
        'http.route': req.route?.path,
        'http.user_agent': req.headers['user-agent'],
        'http.remote_addr': req.ip,
        'request.id': req.id || this.generateCorrelationId(),
      },
    });

    const startTime = Date.now();

    res.on('finish', () => {
      span.setAttributes({
        'http.status_code': res.statusCode,
        'http.response.size': res.get('content-length') || 0,
        'response.time': Date.now() - startTime,
      });

      if (res.statusCode >= 400) {
        span.setStatus({
          code: SpanStatusCode.ERROR,
          message: `HTTP ${res.statusCode}`,
        });
      } else {
        span.setStatus({ code: SpanStatusCode.OK });
      }

      span.end();
    });

    // Continue with request in traced context
    context.with(trace.setSpan(context.active(), span), () => {
      next();
    });
  }

  async traceDatabase<T>(
    operation: string,
    query: string,
    params: any[],
    executor: () => Promise<T>
  ): Promise<T> {
    return this.traceOperation(
      `db.${operation}`,
      async (span) => {
        span.setAttributes({
          'db.operation': operation,
          'db.statement': query,
          'db.params.count': params.length,
          'db.type': 'postgresql',
        });

        const result = await executor();
        
        span.setAttributes({
          'db.result.rows': Array.isArray(result) ? result.length : 1,
        });

        return result;
      },
      {
        'component': 'database',
        'db.sanitized_query': this.sanitizeQuery(query),
      }
    );
  }

  private generateCorrelationId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  private sanitizeQuery(query: string): string {
    // Remove parameter values for security
    return query.replace(/\$\d+/g, '?').replace(/\s+/g, ' ').trim();
  }
}

// Custom metrics collection
class MetricsCollector {
  private metrics = new Map<string, Metric>();
  private timers = new Map<string, Timer>();
  private counters = new Map<string, Counter>();
  private gauges = new Map<string, Gauge>();

  constructor(private exportInterval = 60000) {
    this.startExporter();
  }

  startTimer(name: string, labels?: Record<string, string>): Timer {
    const timer = new Timer(name, labels);
    this.timers.set(`${name}:${JSON.stringify(labels)}`, timer);
    return timer;
  }

  incrementCounter(name: string, value = 1, labels?: Record<string, string>): void {
    const key = `${name}:${JSON.stringify(labels)}`;
    let counter = this.counters.get(key);
    
    if (!counter) {
      counter = new Counter(name, labels);
      this.counters.set(key, counter);
    }
    
    counter.increment(value);
  }

  setGauge(name: string, value: number, labels?: Record<string, string>): void {
    const key = `${name}:${JSON.stringify(labels)}`;
    let gauge = this.gauges.get(key);
    
    if (!gauge) {
      gauge = new Gauge(name, labels);
      this.gauges.set(key, gauge);
    }
    
    gauge.set(value);
  }

  recordHistogram(name: string, value: number, labels?: Record<string, string>): void {
    const key = `${name}:${JSON.stringify(labels)}`;
    let histogram = this.metrics.get(key) as Histogram;
    
    if (!histogram) {
      histogram = new Histogram(name, labels, [
        0.001, 0.01, 0.1, 0.5, 1, 2, 5, 10, 30, 60
      ]);
      this.metrics.set(key, histogram);
    }
    
    histogram.observe(value);
  }

  private startExporter(): void {
    setInterval(() => {
      this.exportMetrics();
    }, this.exportInterval);
  }

  private async exportMetrics(): Promise<void> {
    const allMetrics = {
      counters: Array.from(this.counters.values()).map(c => c.export()),
      gauges: Array.from(this.gauges.values()).map(g => g.export()),
      histograms: Array.from(this.metrics.values()).map(m => m.export()),
      timers: Array.from(this.timers.values()).map(t => t.export()),
      timestamp: Date.now(),
    };

    try {
      // Export to monitoring system (Prometheus, DataDog, etc.)
      await this.sendToMonitoringSystem(allMetrics);
      
      // Clean up old metrics
      this.cleanupMetrics();
    } catch (error) {
      console.error('Failed to export metrics:', error);
    }
  }

  private async sendToMonitoringSystem(metrics: any): Promise<void> {
    // Implementation depends on monitoring system
    // Example: POST to Prometheus pushgateway or DataDog API
    
    if (process.env.MONITORING_ENDPOINT) {
      const response = await fetch(process.env.MONITORING_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(metrics),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to send metrics: ${response.statusText}`);
      }
    }
  }

  private cleanupMetrics(): void {
    const cutoff = Date.now() - 24 * 60 * 60 * 1000; // 24 hours
    
    // Remove old timers that haven't been updated
    for (const [key, timer] of this.timers.entries()) {
      if (timer.getLastUpdate() < cutoff) {
        this.timers.delete(key);
      }
    }
  }
}

class Timer {
  private startTime: number;
  private endTime?: number;
  private lastUpdate: number;

  constructor(private name: string, private labels: Record<string, string> = {}) {
    this.startTime = Date.now();
    this.lastUpdate = this.startTime;
  }

  stop(): number {
    this.endTime = Date.now();
    this.lastUpdate = this.endTime;
    return this.getDuration();
  }

  getDuration(): number {
    const end = this.endTime || Date.now();
    return end - this.startTime;
  }

  getLastUpdate(): number {
    return this.lastUpdate;
  }

  export(): any {
    return {
      name: this.name,
      labels: this.labels,
      duration: this.getDuration(),
      started_at: this.startTime,
      ended_at: this.endTime,
    };
  }
}

class Counter {
  private value = 0;
  private lastUpdate: number = Date.now();

  constructor(private name: string, private labels: Record<string, string> = {}) {}

  increment(value = 1): void {
    this.value += value;
    this.lastUpdate = Date.now();
  }

  getValue(): number {
    return this.value;
  }

  export(): any {
    return {
      name: this.name,
      labels: this.labels,
      value: this.value,
      last_updated: this.lastUpdate,
    };
  }
}

class Gauge {
  private value = 0;
  private lastUpdate: number = Date.now();

  constructor(private name: string, private labels: Record<string, string> = {}) {}

  set(value: number): void {
    this.value = value;
    this.lastUpdate = Date.now();
  }

  increment(value = 1): void {
    this.value += value;
    this.lastUpdate = Date.now();
  }

  decrement(value = 1): void {
    this.value -= value;
    this.lastUpdate = Date.now();
  }

  export(): any {
    return {
      name: this.name,
      labels: this.labels,
      value: this.value,
      last_updated: this.lastUpdate,
    };
  }
}
```