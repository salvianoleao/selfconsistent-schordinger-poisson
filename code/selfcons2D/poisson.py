from dolfin import *
from meshCreator import *
import numpy as np
from scipy import constants as pc

#constants
nd = 1.0e18 * (1e-16) * 1e-6 #1/A^2
e0 = Constant(1.0/8.854188e-22) #Farad per Angstroms
q = Constant(pc.c)
e_g = Constant(13.1)
e_a = Constant((12.248))

qe0 = q/e0

#create mesh
#nx = 40;  ny = 20
mesh = RectangleMesh(x0, y0, xf, yf, nx, ny)


def poissonEq(electronDensity, meshArray):
  
  # Define boundary condition
  # Create classes for defining parts of the boundaries and the interior
  # of the domain
  class Bottom(SubDomain):
    def inside(self, x, on_boundary):
        return near(x[0], x0)
        
  class Top(SubDomain):
     def inside(self, x, on_boundary):
         return near(x[0], xf)
  
  class bAlGaAs1(SubDomain):
     def inside(self, x, on_boundary):
         return near(x[0], gaas_thickness1)
  
         
  class Substrate(SubDomain):
     def inside(self, x, on_boundary):
         return near(x[0], gaas_thickness1 + algaas_thickness1 + algaas_thickness2)
         
  class GaAs1(SubDomain):
    def inside(self, x, on_boundary):
        return between(x[0], (x0, gaas_thickness1))
        
  class AlGaAs1(SubDomain):
      def inside(self, x, on_boundary):
          return (between(x[0], (gaas_thickness1, gaas_thickness1 + algaas_thickness1)))
                
  class AlGaAs2(SubDomain):
      def inside(self, x, on_boundary):
          return (between(x[0], (gaas_thickness1 + algaas_thickness1, gaas_thickness1 + algaas_thickness1 + algaas_thickness2)))
         
  class GaAs2(SubDomain):
     def inside(self, x, on_boundary):
         return between(x[0], (gaas_thickness1 + algaas_thickness1 + algaas_thickness2, xf))
  
  # Sub domain for Periodic boundary condition
  class PeriodicBoundary(SubDomain):
  
    # Left boundary is "target domain" G
    def inside(self, x, on_boundary):
        return bool(x[1] < DOLFIN_EPS and x[1] > -DOLFIN_EPS)

    # Map right boundary (H) to left boundary (G)
    def map(self, x, y):
        y[1] = x[1] - yf -DOLFIN_EPS
        y[0] = x[0]

  # Initialize sub-domain instances
  top = Top()
  bottom = Bottom()
  gaas1 = GaAs1()
  algaas1 = AlGaAs1()
  algaas2 = AlGaAs2()
  gaas2 = GaAs2()
  substrate = Substrate()
  balgaas1 = bAlGaAs1()
  
  
  # Initialize mesh function for interior domains
  domains = CellFunction("size_t", mesh)
  domains.set_all(0)
  gaas1.mark(domains, 1)
  algaas1.mark(domains, 2)
  algaas2.mark(domains, 3)
  gaas2.mark(domains, 4)
  
  
  
  # Initialize mesh function for boundary domains
  boundaries = FacetFunction("size_t", mesh)
  boundaries.set_all(0)
  top.mark(boundaries, 1)
  bottom.mark(boundaries, 2)
  substrate.mark(boundaries, 3)
  balgaas1.mark(boundaries, 4)
  
  #Define Function space
  V =FunctionSpace(mesh, "CG", 1, constrained_domain=PeriodicBoundary())
  
  
  #u0 = Constant('0') 
  #bc = DirichletBC(V, u0, boundary)
  # Define variational problem
  u = TrialFunction(V)
  v = TestFunction(V)
  n = Function(V)
  N_D = Function(V)
  
  #computing the source term -q/epsilon0 (Nd(x) - n(x))
  n.vector()[:] = np.array([i for i in electronDensity])
  N_D.vector()[:] = np.array([nd for i in N_D.vector()])
  
  # Define Dirichlet boundary conditions at top and bottom boundaries
  right = CompiledSubDomain('x[0] == '+str(algaas_thickness2))
  left = CompiledSubDomain('x[0] == '+str(gaas_thickness1))
  bcs = [DirichletBC(V, 0.0, boundaries, 1) , DirichletBC(V, 0.0, boundaries, 2), DirichletBC(V, 1.4, boundaries, 3)]
       
  # Define new measures associated with the interior domains and
  # exterior boundaries
  dx = Measure("dx")[domains]
  ds = Measure("ds")[boundaries]
  
  # Define variational form
  a = inner(e_g*grad(u), grad(v))*dx(1) + inner(e_a*grad(u), grad(v))*dx(2) +  inner(e_a*grad(u), grad(v))*dx(3) +  inner(e_g*grad(u), grad(v))*dx(4)
  
  L = qe0*(N_D-n)*v*dx(1) + qe0*(N_D-n)*v*dx(2) - qe0*n*v*dx(3) - qe0*n*v*dx(4)
  
  # Compute solution
  u = Function(V)
  print 'solving Poisson\'s equation...'
  solve(a == L, u, bcs)
  #plot(u,interactive=True, axes=True)
  
  return u
