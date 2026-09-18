import math
from concreteMaterial import DEFAULT_PLASTICITY
DEFAULT = 0

class Mander:
    def __init__(self, fcm=74.195, fco=74.195, Ec=39350, eco=0.0024, confine_factor=0.8, min_stress=0.002, plasticity=DEFAULT_PLASTICITY):
        self.__fcm = fcm
        self.__fco = fco
        self.__Ec = Ec
        self.__eco = eco
        self.__confine_factor = confine_factor
        self.__min_stress = min_stress
        self.__fcc = self.__calculate_fcc()
        self.__ecc = self.__calculate_ecc()
        self.__Esec = self.__calculate_Esec()
        self.__r = self.__calculate_r()
        self.__x = self.__calculate_x()
        self.__stress = self.__calculate_stress()
        self.__strain = self.__calculate_strain()
        self.__inelastic_strain = self.__calculate_inelastic_strain()
        self.__dc = self.__calculate_dc()
        self.compression_hardening = self.__calculate_compression_hardening()
        self.compression_damage = self.__calculate_compression_damage()
        self.plasticity = plasticity
        if self.plasticity==DEFAULT:
            self.plasticity = self.__calculate_plasticity()
        self.elasticity = ((Ec, 0.2),)
        self.tension = self.__calculate_tension()


    def __calculate_fcc(self):
        fcc = self.__fco * (-1.254 + 2.254 * math.sqrt(1 + 7.94 * self.__confine_factor / self.__fco) - 2 * self.__confine_factor / self.__fco)
        return fcc

    def __calculate_ecc(self):
        ecc = self.__eco * (1 + 5 * (self.__fcc / self.__fco - 1))
        return ecc

    def __calculate_Esec(self):
        Esec = self.__fcc / self.__ecc
        return Esec

    def __calculate_r(self):
        r = self.__Ec / (self.__Ec - self.__Esec)
        return r

    def __calculate_x(self):
        for_x = []
        for i in range(14):
            for_x.append(0.1)
        for i in range(57):
            for_x.append(for_x[-1] * 1.2)

        x = [0.6]
        for i in for_x:
            x.append(x[-1]+i)

        return x

    def __calculate_stress(self):
        stress = []
        for x in self.__x:
            stress.append(self.__fcc * x * self.__r / (self.__r - 1 + x ** self.__r))
        return stress

    def __calculate_strain(self):
        strain = []
        for x in self.__x:
            strain.append(self.__ecc * x)
        return strain

    def __calculate_inelastic_strain(self):
        inelastic_strain = []
        for i, x in enumerate(self.__x):
            inelastic_strain.append(self.__strain[i] - self.__stress[i] / self.__Ec)
        return inelastic_strain

    def __calculate_dc(self):
        dc = []
        for i, x in enumerate(self.__x):
            dc.append(1 - math.sqrt(self.__stress[i] / (self.__strain[i] * self.__Ec)))
        return dc

    def __calculate_compression_hardening(self):
        compression_hardening = []
        for i, stress in enumerate(self.__stress):
            if stress > self.__min_stress :
                compression_hardening.append((stress, self.__inelastic_strain[i]))
        begin = compression_hardening[0]
        compression_hardening[0] = (begin[0], 0)
        return tuple(compression_hardening)

    def __calculate_compression_damage(self):
        compression_damage = []
        for i, stress in enumerate(self.__stress):
            if stress > self.__min_stress :
                compression_damage.append((self.__dc[i], self.__inelastic_strain[i]))
        compression_damage[0]= (0, 0)
        return tuple(compression_damage)

    def __calculate_tension(self):
        ft0 = 2.12 * math.log(1 + 0.1 * self.__fcm)
        Gf = 73 * self.__fcm ** 0.18 * 0.001
        return ((ft0, Gf), )

    def __calculate_plasticity(self):
        #this plasticity from some thesis, not default value in Abaqus
        angle = 40
        eccentricity = 0.1
        fb0fc0 = 1.5 * self.__fco ** (-0.075)
        Kc = 5.5 / (5 + 2 * self.__fco ** 0.075)
        viscosity = 0.001
        return ((angle, eccentricity, fb0fc0, Kc, viscosity),)